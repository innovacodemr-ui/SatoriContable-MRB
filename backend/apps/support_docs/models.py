from django.db import models
from apps.tenants.models import Client
from apps.accounting.models import ThirdParty

class Supplier(ThirdParty):
    class Meta:
        proxy = True
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"

class DianResolution(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='dian_resolutions', null=True, blank=True)
    resolution_number = models.CharField(max_length=100, verbose_name="Número Resolución (Form. 1876)")
    prefix = models.CharField(max_length=10, verbose_name="Prefijo", help_text="Ej: DSE")
    from_number = models.BigIntegerField(verbose_name="Desde")
    to_number = models.BigIntegerField(verbose_name="Hasta")
    current_number = models.BigIntegerField(default=0, verbose_name="Consecutivo Actual")
    start_date = models.DateField(verbose_name="Fecha Inicio Vigencia")
    end_date = models.DateField(verbose_name="Fecha Fin Vigencia")
    technical_key = models.CharField(max_length=255, verbose_name="Llave Técnica DIAN", help_text="Hexadecimal largo proporcionado en la resolución")
    is_active = models.BooleanField(default=True, verbose_name="Activa")

    def __str__(self):
        return f"{self.prefix} {self.resolution_number}"

class SupportDocument(models.Model):
    PAYMENT_METHOD_CHOICES = [('1', 'Contado'), ('2', 'Crédito')]
    STATUS_CHOICES = [('DRAFT', 'Borrador'), ('SENT', 'Enviado'), ('ACCEPTED', 'Aceptado'), ('REJECTED', 'Rechazado')]

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='support_documents')
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='support_documents_as_supplier')
    resolution = models.ForeignKey(DianResolution, on_delete=models.PROTECT, related_name='documents')
    consecutive = models.BigIntegerField(verbose_name="Consecutivo")
    issue_date = models.DateField(verbose_name="Fecha Emisión")
    payment_due_date = models.DateField(verbose_name="Fecha Vencimiento")
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, default='1')
    dian_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT', verbose_name="Estado DIAN")
    cuds = models.CharField(max_length=255, blank=True, null=True, verbose_name="CUDS")
    xml_file = models.FileField(upload_to='support_docs/xml/', blank=True, null=True)
    pdf_file = models.FileField(upload_to='support_docs/pdf/', blank=True, null=True)
    subtotal = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=18, decimal_places=2, default=0)

    class Meta:
        unique_together = ('resolution', 'consecutive')
        verbose_name = "Documento Soporte"
        verbose_name_plural = "Documentos Soporte"

    def __str__(self):
        return f"{self.resolution.prefix}-{self.consecutive}"

class SupportDocumentDetail(models.Model):
    document = models.ForeignKey(SupportDocument, on_delete=models.CASCADE, related_name='details')
    description = models.CharField(max_length=500, verbose_name="Descripción")
    quantity = models.DecimalField(max_digits=18, decimal_places=6, verbose_name="Cantidad")
    unit_price = models.DecimalField(max_digits=18, decimal_places=6, verbose_name="Precio Unitario")
    subtotal = models.DecimalField(max_digits=18, decimal_places=2, verbose_name="Subtotal Línea")
    tax_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0, verbose_name="Impuestos/Retenciones")

    def save(self, *args, **kwargs):
        if not self.subtotal: self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.description} ({self.subtotal})"
