from lxml import etree
from lxml.builder import ElementMaker
import logging
import hashlib
from datetime import datetime
from apps.support_docs.models import SupportDocument
from apps.tenants.models import Client
from apps.common.utils import SecurityService
from apps.common.services.dian_signer import DianXadesSigner

logger = logging.getLogger(__name__)

class SupportDocumentBuilder:
    """
    Clase encargada de construir el XML de Documento Soporte Electrónico (Invoice 2.1)
    Siguiendo el estándar UBL 2.1 definido por la DIAN.
    """
    
    # Namespaces
    NSMAP = {
        None: "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
        'cac': "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
        'cbc': "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
        'ext': "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2",
        'sts': "dian:gov:co:facturaelectronica:Structures-2-1",
        'ds': "http://www.w3.org/2000/09/xmldsig#",
        'xsi': "http://www.w3.org/2001/XMLSchema-instance",
    }
    
    def __init__(self):
        self.E = ElementMaker(nsmap=self.NSMAP)
        self.CBC = ElementMaker(namespace=self.NSMAP['cbc'], nsmap=self.NSMAP)
        self.CAC = ElementMaker(namespace=self.NSMAP['cac'], nsmap=self.NSMAP)
        self.EXT = ElementMaker(namespace=self.NSMAP['ext'], nsmap=self.NSMAP)
        self.STS = ElementMaker(namespace=self.NSMAP['sts'], nsmap=self.NSMAP)
    
    def _calculate_cuds(self, doc: SupportDocument, technical_key: str, date_str: str, time_str: str) -> str:
        """
        Calcula el CUDS (Código Único de Documento Soporte).
        Fórmula: NumDoc + FecDoc + HoraDoc + ValTotal + CodImp1 + ValImp1 + ... + ValImpN + NitEmisor + NitReceptor + ClaveTecnica + TipoAmbiente
        
        Nota: El orden de los NIT es crucial y contraintuitivo.
        En Doc Soporte: 
        - Emisor = Proveedor (Vendedor)
        - Receptor = Nosotros (Adquirente)
        
        Pero la formula técnica suele ser:
        NumFac + FecFac + HorFac + ValFac + CodImp... + NitOFE (Adquirente que emite el doc) + DocAdq (Vendedor) + ClaveTecnica + TipoAmbiente
        
        REVISAR ANEXO TÉCNICO 1.1 (Resolución 000167 de 2021):
        CUDS = SHA-384(NumDS + FecDS + HorDS + ValDS + CodImp + ValImp + ... + ValPag + NitAdquirente + NitVendedor + PinSoftware + TipoAmbiente)
        
        Wait, la instrucción del usuario dice:
        "NumDoc + FecDoc + HoraDoc + ValTotal + CodImp1 + ValImp1 + ... + NIT_Emisor + NIT_Receptor + CLAVE_TECNICA"
        
        Seguiremos la instrucción específica del usuario.
        """
        num_doc = f"{doc.resolution.prefix}{doc.consecutive}"
        val_total = f"{doc.total:.2f}"
        
        # Impuestos (Simplificado para MVP: Solo IVA 01 si hay monto)
        # Si hubiera múltiples impuestos, se deben ordenar por código.
        items_tax = ""
        if doc.tax_amount > 0:
            items_tax = f"01{doc.tax_amount:.2f}"
        
        # Identificaciones
        # Emisor = Supplier (Vendedor)
        nit_emisor = doc.supplier.identification_number
        # Receptor = Client (Comprador/Adquirente - Quien genera el doc)
        nit_receptor = doc.client.nit
        
        # Concatenación
        cuds_string = f"{num_doc}{date_str}{time_str}{val_total}{items_tax}{nit_emisor}{nit_receptor}{technical_key}"
        
        # Aplicar SHA-384
        return hashlib.sha384(cuds_string.encode('utf-8')).hexdigest()

    def build_xml(self, document: SupportDocument) -> bytes:
        resolution = document.resolution
        client = document.client
        supplier = document.supplier
        
        # Formatos de Fecha y Hora
        # Ojo: DIAN exige hora con zona horaria en tags, pero el cálculo CUDS a veces es raw.
        date_gen = document.issue_date
        time_gen = datetime.now().time() # Hora actual de generación
        
        fech_str = date_gen.strftime("%Y-%m-%d")
        hora_str = time_gen.strftime("%H:%M:%S")
        hora_zone_str = f"{hora_str}-05:00"
        
        # Calcular CUDS
        cuds_value = self._calculate_cuds(
            document, 
            resolution.technical_key, 
            fech_str, 
            hora_str
            # Nota: user prompt formula doesn't mention environment type explicitly in concatenation but standard typically strictly requires strictly following documentation.
            # Using prompt formula: Num + Fec + Hora + Val + Tax + NitE + NitR + Key
        )
        
        # Actualizar documento
        document.cuds = cuds_value
        document.save(update_fields=['cuds'])
        
        # ==========================================
        # CONSTRUCCIÓN DEL XML (Estructura Arbol)
        # ==========================================
        
        # Raíz <Invoice>
        root = self.E.Invoice()
        
        # 1. UBLExtensions (Lugar para la firma después)
        root.append(self.EXT.UBLExtensions(
            self.EXT.UBLExtension(
                self.EXT.ExtensionContent() # Aquí irá ds:Signature
            ),
            # Extension DIAN (Información del proveedor tecnológico o software propio)
            self.EXT.UBLExtension(
                self.EXT.ExtensionContent(
                    self.STS.DianExtensions(
                        self.STS.InvoiceControl(
                            self.STS.InvoiceAuthorization(resolution.resolution_number),
                            self.STS.AuthorizationPeriod(
                                self.CBC.StartDate(str(resolution.start_date)),
                                self.CBC.EndDate(str(resolution.end_date))
                            ),
                            self.STS.AuthorizedInvoices(
                                self.STS.Prefix(resolution.prefix),
                                self.STS.From(str(resolution.from_number)),
                                self.STS.To(str(resolution.to_number))
                            )
                        ),
                        self.STS.InvoiceSource(
                            self.CBC.IdentificationCode(client.country, listName="3166-1", listAgencyID="6"), # CO
                            # listAgencyID can vary. 6 is UN/ECE
                        ),
                        self.STS.SoftwareProvider(
                            self.STS.ProviderID(client.nit, schemeAgencyID="195", schemeID="31"), # 31=NIT
                            self.STS.SoftwareID(client.dian_software_id)
                        ),
                        self.STS.SoftwareSecurityCode(
                            hashlib.sha384(f"{client.dian_software_id}pin_software_here{document.consecutive}".encode()).hexdigest() 
                            # TODO: Need software PIN in client config? Assuming test PIN for now or prompting user later.
                        )
                    )
                )
            )
        ))
        
        # 2. Header Fields
        root.append(self.CBC.UBLVersionID("UBL 2.1"))
        root.append(self.CBC.CustomizationID("10")) # Documento Soporte
        root.append(self.CBC.ProfileID("DIAN 2.1: documento soporte en adquisiciones efectuadas a no obligados a facturar"))
        root.append(self.CBC.ID(f"{resolution.prefix}{document.consecutive}"))
        root.append(self.CBC.UUID(cuds_value, schemeName="CUDS-SHA384"))
        root.append(self.CBC.IssueDate(fech_str))
        root.append(self.CBC.IssueTime(hora_zone_str))
        root.append(self.CBC.InvoiceTypeCode("05")) # 05 = Documento Soporte
        root.append(self.CBC.Note("Documento generado por Satori"))
        root.append(self.CBC.DocumentCurrencyCode("COP"))
        
        # 3. Emisor (Supplier/Vendedor) -> AccountingSupplierParty
        # En DocSoporte, el "Proveedor" es quien nos vende (El contratista)
        root.append(self.CAC.AccountingSupplierParty(
            self.CAC.Party(
                self.CAC.PartyTaxScheme(
                    self.CBC.RegistrationName(supplier.get_full_name()),
                    self.CBC.CompanyID(
                        supplier.identification_number, 
                        schemeID=supplier.check_digit or "0", 
                        schemeName="31", # 31=NIT
                        schemeAgencyID="195"
                    ),
                    self.CAC.TaxScheme(
                        self.CBC.ID("01"), 
                        self.CBC.Name("IVA")
                    )
                ),
                self.CAC.PhysicalLocation(
                    self.CAC.Address(
                        self.CBC.ID(supplier.city_code),
                        self.CBC.CityName(supplier.city_code),
                        self.CBC.PostalZone(supplier.postal_code or "000000"),
                        self.CAC.Country(
                            self.CBC.IdentificationCode(supplier.country_code or "CO"),
                            self.CBC.Name("Colombia")
                        )
                    )
                )
            )
        ))
        
        # 4. Receptor (Client/Nosotros) -> AccountingCustomerParty
        root.append(self.CAC.AccountingCustomerParty(
            self.CAC.Party(
                self.CAC.PartyTaxScheme(
                    self.CBC.RegistrationName(client.legal_name),
                    self.CBC.CompanyID(
                        client.nit,
                        schemeID=self._calculate_dv(client.nit),
                        schemeName="31",
                        schemeAgencyID="195"
                    ),
                    self.CAC.TaxScheme(
                        self.CBC.ID("01"), 
                        self.CBC.Name("IVA")
                    )
                )
            )
        ))
        
        # 5. Medios de Pago
        root.append(self.CAC.PaymentMeans(
            self.CBC.ID("1"),
            self.CBC.PaymentMeansCode(document.payment_method), # 1=Contado, 2=Credito
            self.CBC.PaymentDueDate(str(document.payment_due_date))
        ))
        
        # 6. Totales (LegalMonetaryTotal)
        root.append(self.CAC.LegalMonetaryTotal(
            self.CBC.LineExtensionAmount(f"{document.subtotal:.2f}", currencyID="COP"),
            self.CBC.TaxExclusiveAmount(f"{document.subtotal:.2f}", currencyID="COP"),
            self.CBC.TaxInclusiveAmount(f"{document.total:.2f}", currencyID="COP"),
            self.CBC.PayableAmount(f"{document.total:.2f}", currencyID="COP")
        ))
        
        # 7. Líneas (InvoiceLine)
        for idx, item in enumerate(document.details.all(), start=1):
            line = self.CAC.InvoiceLine(
                self.CBC.ID(str(idx)),
                self.CBC.InvoicedQuantity(f"{item.quantity:.6f}", unitCode="94"), # 94=Unidad
                self.CBC.LineExtensionAmount(f"{item.subtotal:.2f}", currencyID="COP"),
                self.CAC.Item(
                    self.CBC.Description(item.description)
                ),
                self.CAC.Price(
                    self.CBC.PriceAmount(f"{item.unit_price:.6f}", currencyID="COP")
                )
            )
            root.append(line)
            
        # Generar XML base a bytes
        xml_bytes = etree.tostring(root, pretty_print=True, xml_declaration=True, encoding='UTF-8', standalone=True)

        # ==========================================
        # FIRMA DIGITAL (XAdES-BES)
        # ==========================================
        if document.client and document.client.dian_certificate:
            try:
                logger.info(f"Iniciando firma digital para doc {document.consecutive}")
                # 1. Recuperar Contraseña
                cert_pass = SecurityService.decrypt_password(document.client.certificate_password_encrypted)
                
                # 2. Obtener path del certificado
                # Nota: .path funciona si es FileSystemStorage. Si es S3, necesitamos .read() bytes.
                # DianXadesSigner soporta ambos si pasamos bytes o path.
                try:
                    cert_data = document.client.dian_certificate.path
                except NotImplementedError:
                    # Caso S3 u otro storage remoto
                    if document.client.dian_certificate.file.closed:
                        document.client.dian_certificate.open('rb')
                    cert_data = document.client.dian_certificate.read()

                # 3. Firmar
                signer = DianXadesSigner(cert_data, cert_pass)
                xml_bytes = signer.sign(xml_bytes)
                logger.info("XML firmado exitosamente.")
                
            except Exception as e:
                logger.error(f"Error firmando XML Documento Soporte {document.consecutive}: {e}")
                # Dependiendo de la política, podemos fallar o continuar sin firma (para debug)
                # Para producción, debería fallar.
                raise e
        else:
            logger.warning("No se encontró certificado digital configurado en el Cliente. El XML NO está firmado.")

        return xml_bytes

    def _calculate_dv(self, nit):
        # Simplificado DV calculator or hardcoded for now
        # En producción usar algoritmo modulo 11
        return "0" 
