import logging
import zipfile
import base64
import requests
import io
from lxml import etree
from datetime import datetime

from apps.support_docs.models import SupportDocument
from apps.support_docs.services.xml_builder import SupportDocumentBuilder
from apps.tenants.models import Client

logger = logging.getLogger(__name__)

class SupportDocumentSender:
    """
    Servicio encargado de enviar el Documento Soporte a la DIAN.
    Maneja compresión ZIP y transporte SOAP (SendTestSetAsync / SendBillAsync).
    """

    # Endpoints DIAN (Facturación / Doc Soporte)
    URL_HABILITACION = "https://vpfe-hab.dian.gov.co/WcfDianCustomerServices.svc"
    URL_PRODUCCION = "https://vpfe.dian.gov.co/WcfDianCustomerServices.svc"

    # Actions SOAP
    ACTION_SEND_TEST_SET = "http://wcf.dian.colombia/IWcfDianCustomerServices/SendTestSetAsync"
    ACTION_SEND_BILL = "http://wcf.dian.colombia/IWcfDianCustomerServices/SendBillAsync"

    NAMESPACE_SOAP = {"soap": "http://www.w3.org/2003/05/soap-envelope", "wcf": "http://wcf.dian.colombia"}
    
    def __init__(self, document: SupportDocument):
        self.document = document
        self.client = document.client
        if not self.client:
             raise ValueError("El documento no tiene asociado un Cliente (Emisor).")

    def send(self):
        """
        Orquesta el proceso completo: Construir -> Firmar -> Zipear -> Enviar -> Procesar Respuesta.
        """
        try:
            logger.info(f"Iniciando envío DIAN Doc Soporte {self.document.consecutive}")
            
            # 1. Construir XML Firmado
            builder = SupportDocumentBuilder()
            xml_signed_bytes = builder.build_xml(self.document) # Ya retorna bytes firmados si hay certificado
            
            if self.document.cuds:
                 # Ensure CUDS is saved if generated
                 pass 

            # 2. Generar Nombre del Archivo (XML y ZIP)
            # Nomenclatura ZIP: z{NitSinDv}000{Consecutive}.zip
            # Nota: El user prompt sugiere 000 + Consecutivo.
            # Estandar real suele ser: "z" + NitOla + Codigo + ConsecutivoHex.
            # Seguiremos instruccion user: z{NIT_SIN_DV}{CODIGO_DOC}{CONSECUTIVO}.zip (CodDoc??)
            # Instruccion 2: "z{NitSinDv}000{Consecutive}.zip"
            
            nit_sender = self.client.nit.split('-')[0]
            # Codigo Interno usuario menciona "000". Usaremos padding zero para consecutivo si es necesario.
            # Ejemplo prompt: z9001234560000000100500001.zip  -> Parece Nit + 0000000100500001 ?
            # Simplificado User Instruction: z{NitSinDv}000{Consecutive}.zip
            
            # Support Doc is type 05. 
            # Usual Facele pattern: z{Nit}{Code(000)}{ConsecutiveHex or similar}
            # Lets stick strictly to: z{NitSinDv}000{Consecutive}.zip as requested explicitly in prompt
            
            zip_filename = f"z{nit_sender}000{self.document.consecutive}.zip"
            xml_filename = f"ds_{self.document.consecutive}.xml" # Name inside zip

            # 3. Comprimir (ZIP on Memory)
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zip_file:
                zip_file.writestr(xml_filename, xml_signed_bytes)
            
            zip_bytes = zip_buffer.getvalue()
            zip_base64 = base64.b64encode(zip_bytes).decode('utf-8')
            
            # Guardamos el ZIP generado para debug (opcional)
            # with open(f"debug_{zip_filename}", "wb") as f:
            #    f.write(zip_bytes)

            # 4. Determinar Endpoint, Método y TestSetId
            # Si tiene dian_test_set_id configurado, es Habilitación -> SendTestSetAsync
            test_set_id = self.client.dian_test_set_id
            
            if test_set_id:
                logger.info(f"Modo Habilitación detectado (TestSetID: {test_set_id})")
                url = self.URL_HABILITACION
                action = self.ACTION_SEND_TEST_SET
                soap_body = self._build_soap_send_test_set(zip_filename, zip_base64, test_set_id)
            else:
                logger.info("Modo Producción (Sin TestSetID)")
                url = self.URL_PRODUCCION
                action = self.ACTION_SEND_BILL
                soap_body = self._build_soap_send_bill(zip_filename, zip_base64)
            
            # 5. Enviar Request SOAP
            headers = {
                'Content-Type': f'application/soap+xml;charset=UTF-8;action="{action}"',
            }
            
            response = requests.post(url, data=soap_body, headers=headers, timeout=60)
            
            if response.status_code != 200:
                logger.error(f"Error HTTP DIAN {response.status_code}: {response.text}")
                self.document.dian_status = 'REJECTED'
                self.document.save()
                return False

            # 6. Procesar Respuesta
            return self._process_response(response.content)

        except Exception as e:
            logger.error(f"Error fatal en SupportDocumentSender: {e}")
            import traceback
            traceback.print_exc()
            self.document.dian_status = 'REJECTED'
            self.document.save()
            return False

    def _build_soap_send_test_set(self, filename, zip_base64, test_set_id):
        return f"""<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:wcf="http://wcf.dian.colombia">
   <soap:Header/>
   <soap:Body>
      <wcf:SendTestSetAsync>
         <wcf:fileName>{filename}</wcf:fileName>
         <wcf:contentFile>{zip_base64}</wcf:contentFile>
         <wcf:testSetId>{test_set_id}</wcf:testSetId>
      </wcf:SendTestSetAsync>
   </soap:Body>
</soap:Envelope>"""

    def _build_soap_send_bill(self, filename, zip_base64):
         return f"""<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:wcf="http://wcf.dian.colombia">
   <soap:Header/>
   <soap:Body>
      <wcf:SendBillAsync>
         <wcf:fileName>{filename}</wcf:fileName>
         <wcf:contentFile>{zip_base64}</wcf:contentFile>
      </wcf:SendBillAsync>
   </soap:Body>
</soap:Envelope>"""

    def _process_response(self, response_content):
        """
        Parsea el XML de respuesta, extrae el ApplicationResponse y verifica 'IsValid'.
        """
        try:
            # Namespaces respuesta
            # Dependiendo del metodo, la respuesta trae wrappers diferentes
            # SendTestSetAsyncResponse > SendTestSetAsyncResult > ZipKey...
            # Pero normalmente DIAN retorna un UploadDocumentResponse de algun tipo.
            
            # Parseamos el Envelope respuesta
            root = etree.fromstring(response_content)
            
            # Buscamos el resultado. 
            # Path comun: Body -> SendTestSetAsyncResponse -> SendTestSetAsyncResult
            ns = self.NAMESPACE_SOAP
            body = root.find("soap:Body", namespaces=ns)
            
            # Check SendTestSetAsyncResult
            result_node = body.find(".//{http://wcf.dian.colombia}SendTestSetAsyncResult")
            if result_node is None:
                 result_node = body.find(".//{http://wcf.dian.colombia}SendBillAsyncResult")
            
            if result_node is None:
                logger.error("No se encontró nodo Result en respuesta DIAN")
                logger.debug(response_content)
                return False

            # Extract fields
            # <wcf:ErrorMessageList .../>
            # <wcf:ZipKey>...</wcf:ZipKey>
            # <wcf:IsValid>true</wcf:IsValid>
            
            # Get IsValid
            is_valid_node = result_node.find("{http://wcf.dian.colombia}IsValid")
            status_message_node = result_node.find("{http://wcf.dian.colombia}StatusMessage")
            error_message_list_node = result_node.find("{http://wcf.dian.colombia}ErrorMessageList") # Complex type
            
            is_valid = is_valid_node.text == 'true' if is_valid_node is not None else False
            status_msg = status_message_node.text if status_message_node is not None else ""
            
            errors = []
            if error_message_list_node is not None:
                # Iterate errors
                pass # Parse detailed errors if needed for feedback
            
            logger.info(f"Respuesta DIAN: IsValid={is_valid}, Msg={status_msg}")

            if is_valid:
                self.document.dian_status = 'SENT' # O 'ACCEPTED' si confirmamos validacion asincrona exitosa inmediada
                # SendTestSetAsync es Async, devuelve un ZipKey.
                # SendBillAsync tambien devuelve ZipKey.
                # Para saber si fue Aceptado realmente, hay que consultar GetStatusZip con el ZipKey.
                # PERO en Doc Soporte a veces SendTestSetAsync responde con validaciones sincronas si falla schema.
                
                # Por ahora marcamos como ENVIADO.
                # Ideal: Guardar ZipKey (TrackId) para consulta posterior.
                self.document.save()
                return True
            else:
                self.document.dian_status = 'REJECTED'
                # Guardar errores en notas?
                self.document.save()
                return False

        except Exception as e:
            logger.error(f"Error procesando respuesta DIAN: {e}")
            return False
