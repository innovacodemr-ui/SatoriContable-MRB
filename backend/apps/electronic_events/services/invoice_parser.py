from lxml import etree
import logging

logger = logging.getLogger(__name__)

class InvoiceParser:
    """
    Clase encargada de extraer datos tácticos del XML de la Factura Electrónica (UBL 2.1).
    Soporta extracción directa de UBL Invoice o extracción desde AttachedDocument.
    """
    
    def __init__(self):
        # Mapa de coordenadas (Namespaces) para navegar el XML
        self.ns = {
            'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
            'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
            'ubl': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2',
            'sts': 'dian:gov:co:facturaelectronica:Structures-2-1',
            'ad': 'urn:oasis:names:specification:ubl:schema:xsd:AttachedDocument-2'
        }

    def parse_invoice_xml(self, xml_content: bytes) -> dict:
        """
        Recibe el contenido del archivo XML (bytes) y retorna un diccionario con la data.
        Maneja AttachedDocument extrayendo la factura contenida si es necesario.
        """
        try:
            parser = etree.XMLParser(recover=True, remove_blank_text=True)
            tree = etree.fromstring(xml_content, parser=parser)
            
            # 0. Detección de AttachedDocument (Contenedor DIAN)
            if 'AttachedDocument' in tree.tag:
                logger.info("AttachedDocument detectado. Extrayendo Invoice...")
                
                # Intentar buscar nodos Invoice hijos directos
                invoice_node = tree.find('.//ubl:Invoice', namespaces=self.ns)
                
                if invoice_node is not None:
                    tree = invoice_node
                else: 
                     # Si no es directo, buscar en Description (Contenedor típico DIAN)
                     description_node = tree.find('.//cac:Attachment/cac:ExternalReference/cbc:Description', namespaces=self.ns)
                     if description_node is not None and description_node.text:
                         try:
                             # El texto es el XML de la factura
                             invoice_xml_str = description_node.text.strip()
                             tree = etree.fromstring(invoice_xml_str.encode('utf-8'), parser=parser)
                             logger.info("Invoice extraído exitosamente de AttachedDocument/Description")
                         except Exception as inner_e:
                             logger.warning(f"No se pudo parsear el contenido de Description como XML: {inner_e}")


            # Verificación rápida: ¿Es una factura (Invoice)? 
            if 'Invoice' not in tree.tag and 'CreditNote' not in tree.tag: 
                 # Podría ser Nota Crédito, soportemoslo a futuro pero advirtamos
                 raise ValueError(f"El XML no es un UBL Invoice válido. Tag raíz: {tree.tag}")

            data = {}

            # 1. Extracción del CUFE (El objetivo principal)
            # El CUFE está en cbc:UUID con schemeName="CUFE-SHA384"
            uuid_node = tree.xpath('//cbc:UUID[@schemeName="CUFE-SHA384"]', namespaces=self.ns)
            if not uuid_node:
                # Fallback: A veces solo viene el UUID sin el atributo schemeName explícito en ciertos proveedores
                uuid_node = tree.xpath('//cbc:UUID', namespaces=self.ns)
            
            data['cufe'] = uuid_node[0].text if uuid_node else None

            # 2. Datos de la Factura
            data['invoice_number'] = self._get_text(tree, '//cbc:ID')
            data['issue_date'] = self._get_text(tree, '//cbc:IssueDate')
            data['issue_time'] = self._get_text(tree, '//cbc:IssueTime')
            
            # 3. Datos del Emisor (Proveedor)
            # Ruta: Invoice -> AccountingSupplierParty -> Party -> PartyTaxScheme -> CompanyID
            data['issuer_nit'] = self._get_text(tree, '//cac:AccountingSupplierParty/cac:Party/cac:PartyTaxScheme/cbc:CompanyID')
            data['issuer_name'] = self._get_text(tree, '//cac:AccountingSupplierParty/cac:Party/cac:PartyTaxScheme/cbc:RegistrationName')
            
            # --- Extracción extendida para creación de proveedores ---
            # Dirección
            data['issuer_address'] = self._get_text(tree, '//cac:AccountingSupplierParty/cac:Party/cac:PartyTaxScheme/cac:RegistrationAddress/cbc:Line')
            data['issuer_city_code'] = self._get_text(tree, '//cac:AccountingSupplierParty/cac:Party/cac:PartyTaxScheme/cac:RegistrationAddress/cbc:ID') 
            data['issuer_city_name'] = self._get_text(tree, '//cac:AccountingSupplierParty/cac:Party/cac:PartyTaxScheme/cac:RegistrationAddress/cbc:CityName')
            data['issuer_department'] = self._get_text(tree, '//cac:AccountingSupplierParty/cac:Party/cac:PartyTaxScheme/cac:RegistrationAddress/cbc:CountrySubentity')
            data['issuer_department_code'] = self._get_text(tree, '//cac:AccountingSupplierParty/cac:Party/cac:PartyTaxScheme/cac:RegistrationAddress/cbc:CountrySubentityCode')
            data['issuer_postal_code'] = self._get_text(tree, '//cac:AccountingSupplierParty/cac:Party/cac:PartyTaxScheme/cac:RegistrationAddress/cbc:PostalZone')
            # Contacto
            data['issuer_email'] = self._get_text(tree, '//cac:AccountingSupplierParty/cac:Party/cac:Contact/cbc:ElectronicMail')
            data['issuer_phone'] = self._get_text(tree, '//cac:AccountingSupplierParty/cac:Party/cac:Contact/cbc:Telephone')
            # ------------------------------------------------------------- 

            # 4. Datos del Receptor (Nosotros/Cliente)
            data['receiver_nit'] = self._get_text(tree, '//cac:AccountingCustomerParty/cac:Party/cac:PartyTaxScheme/cbc:CompanyID')

            # 5. Totales
            # PayableAmount es el total final a pagar (incluyendo impuestos)
            # Mappeamos a 'total_amount' para consistencia con el servicio y modelo
            data['total_amount'] = self._get_text(tree, '//cac:LegalMonetaryTotal/cbc:PayableAmount')
            data['subtotal_amount'] = self._get_text(tree, '//cac:LegalMonetaryTotal/cbc:LineExtensionAmount')
            if not data['subtotal_amount']:
                 data['subtotal_amount'] = '0.00'

            # 6. Impuestos (TaxTotal principal)
            # Tomamos el primero que suele ser el totalizado
            data['tax_amount'] = self._get_text(tree, '//cac:TaxTotal/cbc:TaxAmount')
            if not data['tax_amount']:
                data['tax_amount'] = '0.00'

            return data

        except Exception as e:
            logger.error(f"Error parseando XML: {str(e)}")
            raise e

    def _get_text(self, tree, xpath_query):
        """Helper para extraer texto de forma segura"""
        result = tree.xpath(xpath_query, namespaces=self.ns)
        return result[0].text if result else None
