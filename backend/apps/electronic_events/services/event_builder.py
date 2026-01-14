from lxml import etree
from lxml.builder import ElementMaker
import logging
from datetime import datetime
import pytz

# Tipos de Eventos
EVENT_DEFINITIONS = {
    '030': {'desc': 'Acuse de recibo de Factura Electrónica de Venta', 'code': '030'},
    '032': {'desc': 'Recibo del bien y/o prestación del servicio', 'code': '032'},
    '033': {'desc': 'Aceptación expresa', 'code': '033'},
    '034': {'desc': 'Reclamo de la Factura Electrónica de Venta', 'code': '034'} # Requiere concepto rechazo
}

class ApplicationResponseBuilder:
    """
    Construye el XML ApplicationResponse (UBL 2.1) para eventos de RADIAN.
    Estructura basada en Anexo Técnico DIAN v1.8 (Eventos).
    """
    
    NSMAP = {
        'cac': "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
        'cbc': "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
        'ext': "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2",
        'sts': "dian:gov:co:facturaelectronica:Structures-2-1",
        'ds': "http://www.w3.org/2000/09/xmldsig#",
        'xsi': "http://www.w3.org/2001/XMLSchema-instance",
        None: "urn:oasis:names:specification:ubl:schema:xsd:ApplicationResponse-2"
    }

    def __init__(self):
        self.E = ElementMaker(nsmap=self.NSMAP)
        self.CAC = ElementMaker(namespace=self.NSMAP['cac'], nsmap=self.NSMAP)
        self.CBC = ElementMaker(namespace=self.NSMAP['cbc'], nsmap=self.NSMAP)
        self.EXT = ElementMaker(namespace=self.NSMAP['ext'], nsmap=self.NSMAP)
        self.STS = ElementMaker(namespace=self.NSMAP['sts'], nsmap=self.NSMAP)

    def build_event(self, invoice_event, cude, issue_date, issue_time, event_id):
        """
        Construye el XML para eventos (030, 032, 033).
        El código del evento se toma de invoice_event.event_code.
        """
        code = invoice_event.event_code
        if code not in EVENT_DEFINITIONS:
            raise ValueError(f"Código de evento no soportado: {code}")
            
        def_event = EVENT_DEFINITIONS[code]

        # Datos base
        invoice = invoice_event.invoice
        # Validar si client es None
        client = invoice.client 
        if not client:
             # Fallback ficticio para dev
             raise ValueError("Factura sin cliente asignado")

        # 1. Root ApplicationResponse
        root = self.E.ApplicationResponse()
        
        # 2. UBLExtensions (Placeholder Firma)
        extensions = self.EXT.UBLExtensions(
            self.EXT.UBLExtension(
                self.EXT.ExtensionContent(
                    self.STS.DianExtensions(
                        self.STS.SoftwareProvider(
                            self.STS.ProviderID(
                                client.nit, 
                                schemeID=client.nit.split('-')[1] if '-' in client.nit else '0',
                                schemeName="31",
                                schemeAgencyID="195"
                            ),
                            self.STS.SoftwareID(client.dian_software_id or "c2193b26-538f-4318-97c7-ccda4279774a"), # Default demo
                        ),
                        self.STS.SoftwareSecurityCode("...") 
                    )
                )
            ),
             # Segundo extension para la firma (ds:Signature) se inserta al firmar
             self.EXT.UBLExtension(
                 self.EXT.ExtensionContent()
             )
        )
        root.append(extensions)
        
        # 3. Datos Generales
        root.append(self.CBC.UBLVersionID("UBL 2.1"))
        root.append(self.CBC.CustomizationID("1"))
        root.append(self.CBC.ProfileID("DIAN 2.1: ApplicationResponse de la Factura Electrónica de Venta"))
        
        root.append(self.CBC.ID(event_id))
        
        root.append(self.CBC.UUID(cude, schemeName="CUDE-SHA384"))
        
        root.append(self.CBC.IssueDate(issue_date))
        root.append(self.CBC.IssueTime(issue_time))
        
        root.append(self.CBC.Note(def_event['desc']))
        
        # 4. SenderParty (Nosotros)
        root.append(self.CAC.SenderParty(
            self.CAC.PartyTaxScheme(
                self.CBC.RegistrationName(client.legal_name or client.name),
                self.CBC.CompanyID(
                    client.nit,
                    schemeID=client.nit.split('-')[1] if '-' in client.nit else '0',
                    schemeName="31",
                    schemeAgencyID="195"
                ),
                self.CAC.TaxScheme(
                    self.CBC.ID("01"),
                    self.CBC.Name("IVA")
                )
            )
        ))
        
        # 5. ReceiverParty (El Proveedor)
        root.append(self.CAC.ReceiverParty(
            self.CAC.PartyTaxScheme(
                self.CBC.RegistrationName(invoice.issuer_name),
                self.CBC.CompanyID(
                    invoice.issuer_nit,
                    schemeID="0", 
                    schemeName="31",
                    schemeAgencyID="195"
                ),
                self.CAC.TaxScheme(
                    self.CBC.ID("01"),
                    self.CBC.Name("IVA")
                )
            )
        ))
        
        # 6. DocumentResponse
        root.append(self.CAC.DocumentResponse(
            self.CAC.Response(
                self.CBC.ResponseCode(def_event['code']),
                self.CBC.Description(def_event['desc'])
            ),
            self.CAC.DocumentReference(
                self.CBC.ID(invoice.invoice_number),
                self.CBC.UUID(invoice.cufe, schemeName="CUFE-SHA384")
            )
        ))
        
        return etree.tostring(root, pretty_print=True, xml_declaration=True, encoding='UTF-8')
        
        # 5. ReceiverParty (El Proveedor - Emisor de la factura)
        root.append(self.CAC.ReceiverParty(
            self.CAC.PartyTaxScheme(
                self.CBC.RegistrationName(invoice.issuer_name),
                self.CBC.CompanyID(
                    invoice.issuer_nit,
                    schemeID="0", # TODO: Calcular DV si no lo tenemos parseado
                    schemeName="31",
                    schemeAgencyID="195"
                ),
                self.CAC.TaxScheme(
                    self.CBC.ID("01"),
                    self.CBC.Name("IVA")
                )
            )
        ))
        
        # 6. DocumentResponse (El corazón del evento)
        root.append(self.CAC.DocumentResponse(
            self.CAC.Response(
                self.CBC.ResponseCode(EVENT_DEFINITIONS['030']['code']),
                self.CBC.Description(EVENT_DEFINITIONS['030']['desc'])
            ),
            self.CAC.DocumentReference(
                self.CBC.ID(invoice.invoice_number),
                self.CBC.UUID(invoice.cufe, schemeName="CUFE-SHA384")
            )
        ))
        
        return etree.tostring(root, pretty_print=True, xml_declaration=True, encoding='UTF-8')
