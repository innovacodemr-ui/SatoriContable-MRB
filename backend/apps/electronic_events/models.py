from django.db import models
from apps.tenants.models import Client

class ReceivedInvoice(models.Model):
    """
    Representa una factura recibida de un proveedor (AttachedDocument).
    Satori actúa como buzón, parseando el XML entrante.
    """
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='received_invoices', verbose_name="Adquirente (Nosotros)")
    
    # Datos del Emisor (Proveedor)
    issuer_nit = models.CharField(max_length=20, verbose_name="NIT Proveedor")
    issuer_name = models.CharField(max_length=200, verbose_name="Razón Social Proveedor")
    
    # Datos de la Factura
    invoice_number = models.CharField(max_length=50, verbose_name="Número de Factura")
    cufe = models.CharField(max_length=255, verbose_name="CUFE", unique=True)
    issue_date = models.DateField(verbose_name="Fecha Emisión Factura")
    
    subtotal_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0, verbose_name="Subtotal (Sin Impuestos)")
    tax_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0, verbose_name="Total Impuestos")
    total_amount = models.DecimalField(max_digits=18, decimal_places=2, verbose_name="Total Factura")
    
    # Archivo original
    xml_file = models.FileField(upload_to='inbox/xml/', verbose_name="XML Original")
    pdf_file = models.FileField(upload_to='inbox/pdf/', null=True, blank=True, verbose_name="PDF Representación")
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Factura Recibida"
        verbose_name_plural = "Facturas Recibidas"

    def __str__(self):
        return f"{self.invoice_number} - {self.issuer_name}"

class InvoiceEvent(models.Model):
    """
    Eventos DIAN asociados a una factura recibida.
    Secuencia obligatoria: 030 -> 032 -> 033.
    """
    EVENT_TYPES = [
        ('030', '030 - Acuse de Recibo'),
        ('032', '032 - Recibo del Bien y/o Prestación del Servicio'),
        ('033', '033 - Aceptación Expresa'),
        ('034', '034 - Reclamo (Rechazo)'),
    ]

    DIAN_STATUS_CHOICES = [
        ('PENDING', 'Pendiente'),
        ('SENT', 'Enviado'),
        ('ACCEPTED', 'Aceptado'),
        ('REJECTED', 'Rechazado'),
    ]

    invoice = models.ForeignKey(ReceivedInvoice, on_delete=models.CASCADE, related_name='events')
    event_code = models.CharField(max_length=3, choices=EVENT_TYPES, verbose_name="Código Evento")
    
    # Datos de generación
    consecutive = models.IntegerField(verbose_name="Consecutivo Evento", help_text="Consecutivo único por tipo de evento y emisor")
    issue_date = models.DateTimeField(auto_now_add=True, verbose_name="Fecha Generación")
    
    # Detalles DIAN
    cude = models.CharField(max_length=255, blank=True, verbose_name="CUDE")
    xml_sent = models.FileField(upload_to='events/xml/', blank=True, null=True, verbose_name="XML Evento Enviado")
    dian_status = models.CharField(max_length=20, choices=DIAN_STATUS_CHOICES, default='PENDING')
    dian_message = models.TextField(blank=True, verbose_name="Respuesta DIAN")

    class Meta:
        verbose_name = "Evento Electrónico"
        verbose_name_plural = "Eventos Electrónicos"
        unique_together = ('invoice', 'event_code') # Evitar duplicar el mismo evento para la misma factura (regla de negocio simple)

    def __str__(self):
        return f"{self.event_code} - {self.invoice.invoice_number}"
