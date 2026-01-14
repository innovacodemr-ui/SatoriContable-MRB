from apps.tenants.models import Client
from apps.dian.models import ElectronicDocument
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.backends import default_backend
from lxml import etree
import os

class DianService:
    def __init__(self, client: Client):
        self.client = client

    def get_certificate(self):
        """
        Retrieves the certificate and password for the client.
        """
        if not self.client.dian_certificate:
            raise Exception("Certificate not found for the client.")
        
        pfx_data = self.client.dian_certificate.read()
        # The password should be decrypted before use
        password = self.client.certificate_password_encrypted.encode('utf-8')
        
        try:
            private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(
                pfx_data,
                password,
                default_backend()
            )
            return private_key, certificate
        except Exception as e:
            raise Exception(f"Error parsing certificate: {e}")

    def generate_ubl_xml(self, document: ElectronicDocument) -> etree._Element:
        """
        Generates the UBL XML for the given electronic document.
        This is a placeholder for the actual implementation.
        """
        # This should be a full UBL 2.1 XML structure
        root = etree.Element("Invoice")
        etree.SubElement(root, "ID").text = document.full_number
        etree.SubElement(root, "IssueDate").text = str(document.issue_date)
        return root

    def sign_xml(self, xml_document: etree._Element, private_key, certificate) -> str:
        """
        Signs the given XML document with the private key and certificate.
        This is a placeholder for the actual implementation.
        """
        # This should be a proper XAdES-EPES signature
        # For now, just returning the XML as a string
        return etree.tostring(xml_document, pretty_print=True).decode('utf-8')

    def sign_document(self, document: ElectronicDocument) -> str:
        """
        Signs the given electronic document.
        """
        private_key, certificate = self.get_certificate()
        xml_document = self.generate_ubl_xml(document)
        signed_xml = self.sign_xml(xml_document, private_key, certificate)
        return signed_xml