import imaplib
import email
import os
import zipfile
import io
import base64
import logging
from django.core.files.base import ContentFile
from email.header import decode_header
from django.conf import settings
from apps.tenants.models import Client
from apps.support_docs.models import Supplier
from .invoice_parser import InvoiceParser
from ..models import ReceivedInvoice

logger = logging.getLogger(__name__)

class EmailReceptionService:
    def __init__(self):
        self.host = os.getenv('RECEPTION_EMAIL_HOST', 'imap.gmail.com')
        self.port = int(os.getenv('RECEPTION_EMAIL_PORT', 993))
        self.user = os.getenv('RECEPTION_EMAIL_USER', '')
        self.password = os.getenv('RECEPTION_EMAIL_PASSWORD', '')

    def _save_invoice(self, parser, xml_content):
        # 1. Parsing
        data = parser.parse_invoice_xml(xml_content)
        
        # 2. Routing (Nuevo) - Identificación del Tenant (Empresa)
        receiver_nit = data.get('receiver_nit') 
        if not receiver_nit:
            # Si no hay NIT receptor, podría ser un XML inválido o que el parser no lo halló
            error_msg = "El XML no contiene NIT del Receptor para enrutamiento (AccountingCustomerParty)."
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Limpieza del NIT (Ej: 900123456-1 -> 900123456)
        # Quitamos DV y espacios, puntos si los hubiera
        clean_nit = receiver_nit.split('-')[0].strip().replace('.', '').replace(' ', '')
        
        # Búsqueda de la Empresa (Tenant)
        try:
            # Usamos Client que es el modelo de 'Company' en Satori
            client = Client.objects.get(nit=clean_nit)
        except Client.DoesNotExist:
            error_msg = f"Factura recibida para NIT {clean_nit} (Raw: {receiver_nit}) no registrado en Satori como Empresa."
            logger.warning(error_msg)
            # Lanzamos error para que quede en el log de resultados y no se guarde basura
            raise ValueError(error_msg)

        # 3. Autocrear o Actualizar Proveedor
        # Intentamos buscarlo por NIT
        if data.get('issuer_nit'):
             # Limpieza básica de NIT (quitar DV si viene separado, pero aqui asumimos raw)
             nit = data['issuer_nit']
             
             # Buscar o crear
             supplier, created_supp = Supplier.objects.get_or_create(
                 identification_number=nit,
                 defaults={
                     'identification_type': '31', # Asumimos NIT
                     'business_name': data.get('issuer_name') or 'PROVEEDOR DESCONOCIDO',
                     'party_type': 'PROVEEDOR',
                     'person_type': 1, # Jurídica por defecto, 
                     'email': data.get('issuer_email') or '',
                     'phone': data.get('issuer_phone') or '',
                     'address': data.get('issuer_address') or '',
                     # Campos del modelo ThirdParty (Cuidado con nombres incorrectos)
                     'city_code': data.get('issuer_city_code') or '00000',
                     'department_code': data.get('issuer_department_code') or '00',
                     'postal_code': data.get('issuer_postal_code') or '000000',
                 }
             )
             # Si ya existía, podríamos actualizar datos si vienen vacios... por ahora dejamos asi.

        # Guardar en BD
        # Primero intentamos obtenerla por CUFE para no duplicar
        invoice, created = ReceivedInvoice.objects.get_or_create(
            cufe=data['cufe'],
            defaults={
                'client': client, # Asignado dinámicamente
                'issuer_nit': data['issuer_nit'],
                'issuer_name': data['issuer_name'],
                'invoice_number': data['invoice_number'],
                'issue_date': data['issue_date'],
                'total_amount': data['total_amount'] if data['total_amount'] else 0,
                'subtotal_amount': data['subtotal_amount'] if data.get('subtotal_amount') else 0,
                'tax_amount': data['tax_amount'] if data.get('tax_amount') else 0
            }
        )
        
        if created:
             # Si se creó, guardamos el archivo XML
             # data['invoice_number'] podría tener caracteres raros, mejor limpiar o usar CUFE corto
             filename = f"{data['invoice_number']}.xml"
             invoice.xml_file.save(filename, ContentFile(xml_content))
             invoice.save()

        return invoice
    
    def fetch_invoices(self):
        """
        Conecta al correo, descarga adjuntos XML/ZIP, los procesa y marca como leídos.
        Retorna: { 'processed': int, 'errors': int, 'logs': list }
        """
        results = {'processed': 0, 'errors': 0, 'logs': []}
        
        # Eliminada lógica de 'Client.objects.first()' -> Ahora es Multi-tenant real.

        if not self.user or not self.password:
            results['logs'].append("❌ Error: Credenciales de correo no configuradas en .env")
            return results

        try:
            logger.info(f"Conectando a {self.host}...")
            mail = imaplib.IMAP4_SSL(self.host, self.port)
            mail.login(self.user, self.password)
            mail.select('INBOX')
            
            # Buscar TODOS los correos (ALL) para no depender de si estan leidos o no
            # La marca de leido NO se cambiara gracias a BODY.PEEK[]
            status, messages = mail.search(None, 'ALL')
            
            email_ids = messages[0].split()
            
            BATCH_SIZE = 200
            total_found = len(email_ids)
            
            # Tomar los BATCH_SIZE MAS RECIENTES (ultimos de la lista)
            if total_found > BATCH_SIZE:
                email_ids_to_process = email_ids[-BATCH_SIZE:]
            else:
                email_ids_to_process = email_ids

            # Invertir para procesar lo mas nuevo primero
            email_ids_to_process.reverse()
            
            msg_found = f"📬 Escaneando los {len(email_ids_to_process)} correos más recientes (Total en buzón: {total_found})..."
            results['logs'].append(msg_found)
            logger.info(msg_found)
            
            parser = InvoiceParser()

            for e_id in email_ids_to_process:
                try:
                    # Usar BODY.PEEK[] para NO marcar como leido automáticamente
                    res, msg_data = mail.fetch(e_id, '(BODY.PEEK[])')
                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_bytes(response_part[1])
                            subject, encoding = decode_header(msg["Subject"])[0]
                            if isinstance(subject, bytes) and encoding:
                                subject = subject.decode(encoding)
                            
                            has_invoice = False
                            
                            # Recorrer adjuntos
                            for part in msg.walk():
                                if part.get_content_maintype() == 'multipart':
                                    continue
                                if part.get('Content-Disposition') is None:
                                    continue
                                
                                filename = part.get_filename()
                                if not filename:
                                    continue
                                    
                                content = part.get_payload(decode=True)
                                
                                if filename.lower().endswith('.xml'):
                                    # Procesar XML
                                    try:
                                        self._save_invoice(parser, content)
                                        results['processed'] += 1
                                        has_invoice = True
                                        results['logs'].append(f"✅ Factura procesada: {filename}")
                                    except Exception as e:
                                        msg_err = f"Error parseando {filename}: {str(e)}"
                                        logger.error(msg_err)
                                        results['logs'].append(f"⚠️ {msg_err}")
                                        results['errors'] += 1

                                elif filename.lower().endswith('.zip'):
                                    # Procesar ZIP
                                    try:
                                        with zipfile.ZipFile(io.BytesIO(content)) as z:
                                            for zfilename in z.namelist():
                                                if zfilename.lower().endswith('.xml'):
                                                    xml_data = z.read(zfilename)
                                                    # Basic validation often 'AttachedDocument'
                                                    if b'AttachedDocument' in xml_data or b'Invoice' in xml_data:
                                                        self._save_invoice(parser, xml_data)
                                                        results['processed'] += 1
                                                        has_invoice = True
                                                        results['logs'].append(f"✅ Factura (ZIP) procesada: {zfilename}")
                                    except Exception as e:
                                        msg_err = f"Error procesando ZIP {filename}: {str(e)}"
                                        results['logs'].append(f"⚠️ {msg_err}")
                                        results['errors'] += 1
                            
                            # Si no se encontró factura, tal vez no marcar como leído?
                            # O marcarlo para no procesar de nuevo.
                            # mail.store(e_id, '+FLAGS', '\\Seen') 
                
                except Exception as e:
                    logger.error(f"Error procesando email ID {e_id}: {e}")
                    results['errors'] += 1

            mail.close()
            mail.logout()
            
        except Exception as e:
            logger.error(f"Error general en EmailReceptionService: {e}")
            results['logs'].append(f"❌ Error de conexión: {str(e)}")
        
        return results
