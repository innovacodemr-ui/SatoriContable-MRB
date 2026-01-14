from django.db import models, transaction
from decimal import Decimal
from fernet_fields import EncryptedCharField
from apps.tenants.models import Client
from apps.accounting.models import ThirdParty, CostCenter
from django.utils.translation import gettext_lazy as _
from datetime import date
from apps.common.managers import TenantAwareManager

# ==============================================================================
#  MODELOS DE CONFIGURACIÓN FISCAL Y SEGURIDAD (DIAN)
# ==============================================================================

class ElectronicBillingConfig(models.Model):
    """
    Configuración global de facturación electrónica por Cliente (Tenant).
    Almacena credenciales sensibles ENCRIPTADAS.
    """
    ENVIRONMENT_CHOICES = [
        ('PRUEBAS', 'Habilitación / Pruebas'),
        ('PRODUCCION', 'Producción'),
    ]

    client = models.OneToOneField(
        Client,
        on_delete=models.CASCADE,
        related_name='electronic_billing_config',
        verbose_name=_("Cliente")
    )

    environment = models.CharField(
        max_length=20,
        choices=ENVIRONMENT_CHOICES,
        default='PRUEBAS',
        verbose_name=_("Ambiente DIAN")
    )
    software_id = models.CharField(
        max_length=255,
        verbose_name=_("ID de Software"),
        help_text=_("Identificador único del software proporcionado por la DIAN")
    )
    software_pin = EncryptedCharField(
        max_length=100,
        verbose_name=_("PIN del Software"),
        help_text=_("PIN secreto entregado por la DIAN. Se guarda encriptado.")
    )
    certificate_file = models.FileField(
        upload_to='private/certs/',
        verbose_name=_("Certificado Digital (.p12)"),
        help_text=_("Archivo de firma digital emitido por una entidad certificadora (GSE, Andes, etc).")
    )
    certificate_password = EncryptedCharField(
        max_length=255,
        verbose_name=_("Contraseña Certificado"),
        help_text=_("Contraseña para desencriptar la llave privada del certificado.")
    )
    invoice_test_set_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("Test Set ID (Facturación)"),
        help_text=_("Identificador del set de pruebas para Factura Electrónica")
    )
    payroll_test_set_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("Test Set ID (Nómina)"),
        help_text=_("Identificador del set de pruebas para Nómina Electrónica")
    )
    support_doc_test_set_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("Test Set ID (Doc. Soporte)"),
        help_text=_("Identificador del set de pruebas para Documento Soporte")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Fecha Creación"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Última Actualización"))

    objects = TenantAwareManager()

    class Meta:
        verbose_name = _("Configuración Fiscal (DIAN)")
        verbose_name_plural = _("Configuraciones Fiscales")

    def __str__(self):
        return f"Config DIAN: {self.client} ({self.environment})"


class DianResolution(models.Model):
    """
    Resoluciones de numeración autorizadas oficialmente por la DIAN.
    """
    DOCUMENT_TYPE_CHOICES = [
        ('INVOICE', 'Factura Electrónica de Venta'),
        ('POS', 'Factura Electrónica POS'),
        ('SUPPORT_DOCUMENT', 'Documento Soporte en Adquisiciones'),
    ]

    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='invoicing_dian_resolutions',
        verbose_name=_("Cliente")
    )

    document_type = models.CharField(
        max_length=30,
        choices=DOCUMENT_TYPE_CHOICES,
        default='INVOICE',
        verbose_name=_("Tipo de Documento")
    )
    prefix = models.CharField(
        max_length=10,
        blank=True,
        verbose_name=_("Prefijo"),
        help_text=_("Ej: SETT. Dejar en blanco si no tiene prefijo.")
    )
    resolution_number = models.CharField(
        max_length=100,
        verbose_name=_("Número de Resolución"),
        help_text=_("Número oficial del formulario 1876")
    )
    date_from = models.DateField(verbose_name=_("Fecha Inicio Vigencia"))
    date_to = models.DateField(verbose_name=_("Fecha Fin Vigencia"))
    number_from = models.BigIntegerField(verbose_name=_("Rango Desde"))
    number_to = models.BigIntegerField(verbose_name=_("Rango Hasta"))
    current_number = models.BigIntegerField(
        verbose_name=_("Consecutivo Actual"),
        help_text=_("El próximo documento tomará este número + 1 (o este número si no se ha usado).")
    )
    technical_key = EncryptedCharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_("Clave Técnica"),
        help_text=_("Clave técnica de la resolución. Se guarda encriptada.")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Activa")
    )

    objects = TenantAwareManager()

    class Meta:
        verbose_name = _("Resolución DIAN")
        verbose_name_plural = _("Resoluciones DIAN")
        ordering = ['-date_from']
        unique_together = ('client', 'prefix', 'document_type')

    def get_next_number(self):
        """
        Atomically increments and returns the next number in the sequence.
        """
        with transaction.atomic():
            resolution = DianResolution.objects.select_for_update().get(pk=self.pk)
            resolution.current_number += 1
            resolution.save()
            return resolution.current_number

    def __str__(self):
        return f"{self.get_document_type_display()} - {self.prefix} {self.number_from}-{self.number_to}"


class DocumentSequence(models.Model):
    """
    Control de numeración interna para documentos que NO requieren resolución DIAN.
    """
    SEQUENCE_TYPE_CHOICES = [
        ('PAYROLL', 'Nómina Electrónica'),
        ('PAYROLL_ADJUSTMENT', 'Nota de Ajuste de Nómina'),
        ('CREDIT_NOTE', 'Nota Crédito'),
        ('DEBIT_NOTE', 'Nota Débito'),
    ]

    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='document_sequences',
        verbose_name=_("Cliente")
    )

    document_type = models.CharField(
        max_length=30,
        choices=SEQUENCE_TYPE_CHOICES,
        verbose_name=_("Tipo de Documento")
    )
    prefix = models.CharField(
        max_length=10,
        blank=True,
        verbose_name=_("Prefijo Interno"),
        help_text=_("Opcional. Ej: NC, NE.")
    )
    current_number = models.BigIntegerField(
        default=0,
        verbose_name=_("Consecutivo Actual")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Activo")
    )

    objects = TenantAwareManager()

    class Meta:
        verbose_name = _("Secuencia de Documentos")
        verbose_name_plural = _("Secuencias de Documentos")
        unique_together = ['client', 'document_type', 'prefix']

    def get_next_number(self):
        """
        Atomically increments and returns the next number in the sequence.
        """
        with transaction.atomic():
            sequence = DocumentSequence.objects.select_for_update().get(pk=self.pk)
            sequence.current_number += 1
            sequence.save()
            return sequence.current_number

    def __str__(self):
        return f"{self.get_document_type_display()} (Actual: {self.current_number})"

# ==============================================================================
#  MODELOS DE NEGOCIO (FACTURAS, PRODUCTOS, ETC)
# ==============================================================================

class SupportDocument(models.Model):
    """
    Documento Soporte en Adquisiciones a no Obligados a Facturar.
    """
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='invoicing_support_documents')
    resolution = models.ForeignKey(DianResolution, on_delete=models.PROTECT, related_name='support_documents', verbose_name=_("Resolución"))
    supplier = models.ForeignKey(ThirdParty, on_delete=models.PROTECT, related_name='support_purchases', verbose_name=_("Proveedor"))
    prefix = models.CharField(max_length=10)
    consecutive = models.BigIntegerField()
    issue_date = models.DateField(verbose_name=_("Fecha Emisión"))
    payment_due_date = models.DateField(verbose_name=_("Fecha Vencimiento"))
    delivery_date = models.DateField(null=True, blank=True, verbose_name=_("Fecha Recepción"))
    currency = models.CharField(max_length=3, default='COP')
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    STATUS_CHOICES = [
        ('DRAFT', 'Borrador'),
        ('SIGNED', 'Firmado'),
        ('SENT', 'Enviado'),
        ('ACCEPTED', 'Aceptado por DIAN'),
        ('REJECTED', 'Rechazado'),
    ]
    dian_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    cuds = models.CharField(max_length=255, blank=True, verbose_name="CUDS (Código Único)")
    xml_file = models.FileField(upload_to='support_docs/xml/', blank=True, null=True)
    dian_response = models.JSONField(default=dict, blank=True, verbose_name="Respuesta DIAN")
    notes = models.TextField(blank=True, verbose_name="Notas")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantAwareManager()

    class Meta:
        verbose_name = "Documento Soporte"
        verbose_name_plural = "Documentos Soporte"
        unique_together = ('client', 'prefix', 'consecutive')

    def __str__(self):
        return f"DS-{self.prefix}{self.consecutive} - {self.supplier.name}"


class SupportDocumentDetail(models.Model):
    document = models.ForeignKey(SupportDocument, on_delete=models.CASCADE, related_name='items')
    
    # --- CAMPO NUEVO PARA CENTRO DE COSTOS ---
    cost_center = models.ForeignKey(
        CostCenter, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name=_("Centro de Costo")
    )
    # -----------------------------------------

    code = models.CharField(max_length=50, blank=True, verbose_name="Código Item")
    description = models.CharField(max_length=500, verbose_name="Descripción")
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=14, decimal_places=2, verbose_name="Precio Unitario")
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Porcentaje IVA (0, 5, 19)")
    total_line = models.DecimalField(max_digits=14, decimal_places=2)

    def save(self, *args, **kwargs):
        self.total_line = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class Item(models.Model):
    """
    Maestro de Productos y Servicios (Inventario)
    """
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='items')
    TYPE_CHOICES = [
        ('PRODUCTO', 'Producto (Bien)'),
        ('SERVICIO', 'Servicio'),
    ]
    TAX_TYPE_CHOICES = [
        ('IVA_19', 'IVA General 19%'),
        ('IVA_5', 'IVA Reducido 5%'),
        ('EXENTO', 'Exento (0%)'),
        ('EXCLUIDO', 'Excluido (Sin IVA)'),
    ]
    code = models.CharField(max_length=50, verbose_name="Código")
    description = models.CharField(max_length=255, verbose_name="Descripción")
    unit_price = models.DecimalField(max_digits=14, decimal_places=2, verbose_name="Precio Venta")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='SERVICIO', verbose_name="Tipo")
    tax_type = models.CharField(max_length=20, choices=TAX_TYPE_CHOICES, default='IVA_19', verbose_name="Tipo Impuesto")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantAwareManager()

    class Meta:
        verbose_name = "Producto/Servicio"
        verbose_name_plural = "Productos y Servicios"
        ordering = ['code']
        unique_together = ('client', 'code')

    def __str__(self):
        return f"{self.client.nit} - {self.code} - {self.description}"


class Invoice(models.Model):
    """
    Factura de Venta (Operativa/Comercial).
    """
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='invoices')
    resolution = models.ForeignKey(DianResolution, on_delete=models.PROTECT, related_name='invoices')
    customer = models.ForeignKey(ThirdParty, on_delete=models.PROTECT, related_name='invoices', verbose_name="Cliente")
    prefix = models.CharField(max_length=10)
    number = models.BigIntegerField(verbose_name="Número")
    issue_date = models.DateField(default=date.today, verbose_name="Fecha Emisión")
    payment_due_date = models.DateField(verbose_name="Fecha Vencimiento")
    PAYMENT_TERM_CHOICES = [
        ('CONTADO', 'De Contado'),
        ('30_DIAS', 'Crédito 30 Días'),
        ('60_DIAS', 'Crédito 60 Días'),
    ]
    payment_term = models.CharField(max_length=20, choices=PAYMENT_TERM_CHOICES, default='CONTADO')
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    STATUS_CHOICES = [
        ('DRAFT', 'Borrador'),
        ('POSTED', 'Guardada / Por Emitir'),
        ('SENT', 'Enviada a DIAN'),
        ('ACCEPTED', 'Aceptada por DIAN'),
        ('REJECTED', 'Rechazada por DIAN'),
        ('VOID', 'Anulada'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    
    # Campos DIAN
    cufe = models.CharField(max_length=255, null=True, blank=True, verbose_name="CUFE")
    xml_file = models.FileField(upload_to='invoices/xml/', null=True, blank=True, verbose_name="XML Firmado")
    dian_response = models.JSONField(null=True, blank=True, verbose_name="Respuesta DIAN")
    
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantAwareManager()

    class Meta:
        verbose_name = "Factura de Venta"
        verbose_name_plural = "Facturas de Venta"
        unique_together = ('client', 'prefix', 'number')

    def __str__(self):
        return f"{self.prefix}{self.number} - {self.customer.business_name if self.customer.business_name else self.customer.first_name}"


class InvoiceLine(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='lines')
    item = models.ForeignKey(Item, on_delete=models.PROTECT, null=True, blank=True)
    
    # --- CAMPO NUEVO PARA CENTRO DE COSTOS ---
    cost_center = models.ForeignKey(
        CostCenter, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name=_("Centro de Costo")
    )
    # -----------------------------------------

    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=14, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0) # 19.00
    subtotal = models.DecimalField(max_digits=14, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2)
    total = models.DecimalField(max_digits=14, decimal_places=2)

    def save(self, *args, **kwargs):
        self.quantity = Decimal(str(self.quantity))
        self.unit_price = Decimal(str(self.unit_price))
        self.tax_rate = Decimal(str(self.tax_rate))
        self.subtotal = self.quantity * self.unit_price
        self.tax_amount = self.subtotal * (self.tax_rate / Decimal(100))
        self.total = self.subtotal + self.tax_amount
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.description} ({self.total_line})"

