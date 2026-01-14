import os
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from apps.invoicing.models import ElectronicBillingConfig
from lxml import etree
from signxml import XMLSigner, methods
import OpenSSL.crypto

class DianService:
    def __init__(self, client):
        self.client = client
        self.config = self._get_config()

    def _get_config(self):
        try:
            return ElectronicBillingConfig.objects.get(client=self.client)
        except ElectronicBillingConfig.DoesNotExist:
            raise ImproperlyConfigured(f"El cliente {self.client} no tiene configuración de Facturación Electrónica.")

    def get_certificate_and_key(self):
        """
        Carga el certificado y la llave privada desde el archivo .p12
        """
        if not self.config.certificate_file:
            raise ImproperlyConfigured("No hay archivo de certificado cargado.")
        
        # Leer archivo .p12
        p12_path = self.config.certificate_file.path
        if not os.path.exists(p12_path):
            raise ImproperlyConfigured(f"El archivo de certificado no existe en la ruta: {p12_path}")
            
        with open(p12_path, 'rb') as f:
            p12_data = f.read()

        # Obtener password desencriptado
        password = self.config.certificate_password
        if not password:
             raise ImproperlyConfigured("La contraseña del certificado no está configurada.")
        
        # Cargar PKCS12
        try:
            p12 = OpenSSL.crypto.load_pkcs12(p12_data, password.encode('utf-8'))
            cert = p12.get_certificate()
            key = p12.get_privatekey()
            return cert, key
        except Exception as e:
            raise ImproperlyConfigured(f"Error al cargar/desencriptar el certificado: {str(e)}")

    def sign_xml(self, xml_etree):
        """
        Firma un objeto etree.Element usando XAdES-BES
        """
        cert, key = self.get_certificate_and_key()
        
        # Convertir a formato que signxml entiende (PEM)
        cert_pem = OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, cert)
        key_pem = OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_PEM, key)

        signer = XMLSigner(
            method=methods.enveloped,
            signature_algorithm='rsa-sha256',
            digest_algorithm='sha256',
            c14n_algorithm='http://www.w3.org/TR/2001/REC-xml-c14n-20010315'
        )
        
        # Firmar
        signed_xml = signer.sign(
            xml_etree,
            key=key_pem,
            cert=cert_pem,
            always_add_key_value=True # DIAN a veces requiere RSAKeyValue
        )
        
        return signed_xml

    def generate_invoice_xml(self, invoice):
        """
        Genera un XML UBL 2.1 básico para la factura.
        Este es un esqueleto para pruebas de firma.
        """
        nsmap = {
            'fe': 'http://www.dian.gov.co/contratos/facturaelectronica/v1',
            'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
            'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
        }
        
        # Root Element: Invoice
        invoice_xml = etree.Element('{urn:oasis:names:specification:ubl:schema:xsd:Invoice-2}Invoice', nsmap=nsmap)
        
        # ID (Número de Factura)
        xml_id = etree.SubElement(invoice_xml, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID')
        xml_id.text = f"{invoice.prefix}{invoice.number}"
        
        # Date
        issue_date = etree.SubElement(invoice_xml, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}IssueDate')
        issue_date.text = str(invoice.issue_date)
        
        # Supplier (Emisor)
        supplier = etree.SubElement(invoice_xml, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}AccountingSupplierParty')
        party = etree.SubElement(supplier, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}Party')
        party_name = etree.SubElement(party, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PartyName')
        name = etree.SubElement(party_name, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}Name')
        name.text = invoice.client.name
        
        # Customer (Receptor)
        customer = etree.SubElement(invoice_xml, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}AccountingCustomerParty')
        party_cust = etree.SubElement(customer, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}Party')
        party_name_cust = etree.SubElement(party_cust, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PartyName')
        name_cust = etree.SubElement(party_name_cust, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}Name')
        name_cust.text = invoice.customer.business_name or invoice.customer.first_name
        
        # Totals
        legal_monetary_total = etree.SubElement(invoice_xml, '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}LegalMonetaryTotal')
        payable_amount = etree.SubElement(legal_monetary_total, '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}PayableAmount', currencyID="COP")
        payable_amount.text = str(invoice.total)
        
        return invoice_xml
