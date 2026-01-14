import logging
from lxml import etree
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.primitives import serialization
from signxml import XMLSigner, methods

logger = logging.getLogger(__name__)

class DianXadesSigner:
    """
    Clase reutilizable para firmar XMLs (UBL 2.1) con XAdES-BES.
    Utilizado para Nómina Electrónica, Factura y Documento Soporte.
    """

    def __init__(self, cert_data, cert_password: str):
        """
        :param cert_data: Bytes del archivo .p12 o string ruta al archivo
        :param cert_password: Contraseña del certificado
        """
        self.cert_data = cert_data
        self.cert_password = cert_password

    def sign(self, xml_bytes: bytes) -> bytes:
        """
        Injects the signature into the UBLExtensions/ExtensionContent of the provided XML.
        """
        try:
            # 1. Load Certificate and Private Key
            p12_data = self.cert_data
            if isinstance(self.cert_data, str):
                # If it's a path, read it
                with open(self.cert_data, "rb") as f:
                    p12_data = f.read()

            p12 = pkcs12.load_key_and_certificates(p12_data, self.cert_password.encode())
            
            key = p12[0]
            cert = p12[1]

            if not key or not cert:
                 raise ValueError("El archivo .p12 no contiene llave privada o certificado válidos.")

            # 2. Prepare for signxml
            key_pem = key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            )
            cert_pem = cert.public_bytes(serialization.Encoding.PEM)

            # 3. Configure Signer (RSA-SHA256)
            # method=methods.enveloped is standard for XAdES where signature is inside the doc
            signer = XMLSigner(
                method=methods.enveloped,
                signature_algorithm="rsa-sha256",
                digest_algorithm="sha256",
                c14n_algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315"
            )

            # 4. Sign
            # signxml returns a new etree element with the signature appended (usually at end or by ID)
            root = etree.fromstring(xml_bytes)
            
            # Note: valid_ubl ensures we don't break UBL structure if possible, but signxml operates on XML structure
            signed_root = signer.sign(
                root, 
                key=key_pem, 
                cert=cert_pem,
                always_add_key_value=False # X509Data/X509Certificate is enough usually
            )

            # 5. Move Signature to UBLExtensions (DIAN Requirement)
            # The signature must be inside: 
            # <ext:UBLExtensions>
            #   <ext:UBLExtension>
            #     <ext:ExtensionContent>
            #       <ds:Signature> ... </ds:Signature>
            #     </ext:ExtensionContent>
            #   </ext:UBLExtension>
            # </ext:UBLExtensions>
            
            # Namespace mapping defined in the XML usually
            ns = {
                'ds': 'http://www.w3.org/2000/09/xmldsig#', 
                'ext': 'urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2'
            }
            
            signature = signed_root.find("ds:Signature", namespaces=ns)
            
            # Find the UBLExtensions block. If not present, we might need to create it, 
            # but standard builders (like Payroll or SupportDoc) usually create the placeholder.
            # We look for the FIRST UBLExtension that is empty or specifically designated for signature.
            # However, simpler logic: Append to the Extensions container.
            
            extensions = signed_root.find("ext:UBLExtensions", namespaces=ns)
            
            if signature is not None:
                if extensions is None:
                    # If no extensions block, create one at the beginning (child 0)
                    extensions = etree.Element("{urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2}UBLExtensions")
                    signed_root.insert(0, extensions)

                # Create new UBLExtension for the signature
                extension = etree.SubElement(extensions, "{urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2}UBLExtension")
                content = etree.SubElement(extension, "{urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2}ExtensionContent")
                
                # Move signature inside content
                content.append(signature)

            # Return serialized bytes
            return etree.tostring(signed_root, pretty_print=True, xml_declaration=True, encoding='UTF-8', standalone=True)

        except Exception as e:
            logger.error(f"Error firmando XML: {str(e)}")
            raise e
