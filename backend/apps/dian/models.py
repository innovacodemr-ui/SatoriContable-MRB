from django.db import models
from django.contrib.auth.models import User
from apps.accounting.models import ThirdParty, Account
from decimal import Decimal


class ElectronicDocument(models.Model):
    """
    Documento Electrónico base para facturación electrónica DIAN.
    """
    DOCUMENT_TYPE_CHOICES = [
        ('INVOICE', 'Factura de Venta'),
        ('CREDIT_NOTE', 'Nota Crédito'),
        ('DEBIT_NOTE', 'Nota Débito'),
        ('PAYROLL', 'Nómina Electrónica'),
        ('SUPPORT_DOCUMENT', 'Documento Soporte'),
    ]
    
    STATUS_CHOICES = [
        ('DRAFT', 'Borrador'),
        ('PENDING', 'Pendiente de Envío'),
        ('SENT', 'Enviado a DIAN'),
        ('ACCEPTED', 'Aceptado por DIAN'),
        ('REJECTED', 'Rechazado por DIAN'),
        ('CANCELLED', 'Anulado'),
    ]
    
    # Información básica
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES, verbose_name="Tipo de Documento")
    prefix = models.CharField(max_length=10, blank=True, verbose_name="Prefijo")
    number = models.CharField(max_length=50, verbose_name="Número")
    full_number = models.CharField(max_length=60, unique=True, verbose_name="Número Completo")  # prefix + number
    
    # Fechas
    issue_date = models.DateField(verbose_name="Fecha de Emisión")
    due_date = models.DateField(null=True, blank=True, verbose_name="Fecha de Vencimiento")
    
    # CUFE/CUDE (Código Único de Facturación Electrónica)
    cufe = models.CharField(max_length=255, blank=True, unique=True, verbose_name="CUFE/CUDE")
    
    # QR Code
    qr_code = models.TextField(blank=True, verbose_name="Código QR")
    
    # Cliente
    customer = models.ForeignKey(
        ThirdParty,
        on_delete=models.PROTECT,
        related_name='electronic_documents',
        verbose_name="Cliente"
    )
    
    # Moneda
    currency = models.CharField(max_length=3, default='COP', verbose_name="Moneda")
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=4, default=1, verbose_name="Tasa de Cambio")
    
    # Totales
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Subtotal")
    tax_total = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Total Impuestos")
    discount_total = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Total Descuentos")
    total = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Total")
    
    # Información de pago
    PAYMENT_METHOD_CHOICES = [
        ('CASH', 'Efectivo'),
        ('CARD', 'Tarjeta'),
        ('TRANSFER', 'Transferencia'),
        ('CHECK', 'Cheque'),
        ('CREDIT', 'Crédito'),
    ]
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='CASH',
        verbose_name="Método de Pago"
    )
    payment_terms = models.CharField(max_length=200, blank=True, verbose_name="Términos de Pago")
    
    # Estado DIAN
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT', verbose_name="Estado")
    dian_response = models.JSONField(null=True, blank=True, verbose_name="Respuesta DIAN")
    dian_sent_at = models.DateTimeField(null=True, blank=True, verbose_name="Enviado a DIAN")
    dian_accepted_at = models.DateTimeField(null=True, blank=True, verbose_name="Aceptado por DIAN")
    
    # Archivos
    xml_file = models.FileField(upload_to='dian/xml/', blank=True, null=True, verbose_name="Archivo XML")
    pdf_file = models.FileField(upload_to='dian/pdf/', blank=True, null=True, verbose_name="Archivo PDF")
    attached_document = models.FileField(upload_to='dian/attachments/', blank=True, null=True, verbose_name="Documento Adjunto")
    
    # Notas
    notes = models.TextField(blank=True, verbose_name="Notas")
    internal_notes = models.TextField(blank=True, verbose_name="Notas Internas")
    
    # Usuario responsable
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='electronic_documents_created',
        verbose_name="Creado por"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Metadata adicional
    metadata = models.JSONField(default=dict, blank=True, verbose_name="Metadatos")

    class Meta:
        verbose_name = "Documento Electrónico"
        verbose_name_plural = "Documentos Electrónicos"
        ordering = ['-issue_date', '-number']
        indexes = [
            models.Index(fields=['full_number']),
            models.Index(fields=['issue_date']),
            models.Index(fields=['status']),
            models.Index(fields=['cufe']),
            models.Index(fields=['customer']),
        ]

    def __str__(self):
        return f"{self.get_document_type_display()} {self.full_number}"
    
    def save(self, *args, **kwargs):
        # Generar número completo
        if self.prefix:
            self.full_number = f"{self.prefix}{self.number}"
        else:
            self.full_number = self.number
        super().save(*args, **kwargs)


class ElectronicDocumentLine(models.Model):
    """
    Línea de Documento Electrónico.
    """
    document = models.ForeignKey(
        ElectronicDocument,
        on_delete=models.CASCADE,
        related_name='lines',
        verbose_name="Documento"
    )
    line_number = models.IntegerField(verbose_name="Línea")
    
    # Producto/Servicio
    product_code = models.CharField(max_length=50, verbose_name="Código del Producto")
    product_name = models.CharField(max_length=300, verbose_name="Nombre del Producto")
    description = models.TextField(blank=True, verbose_name="Descripción")
    
    # Cantidad y precios
    quantity = models.DecimalField(max_digits=10, decimal_places=3, default=1, verbose_name="Cantidad")
    unit_of_measure = models.CharField(max_length=10, default='UND', verbose_name="Unidad de Medida")
    unit_price = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Precio Unitario")
    
    # Descuentos
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="% Descuento"
    )
    discount_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Descuento")
    
    # Subtotal antes de impuestos
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Subtotal")
    
    # Impuestos
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="% IVA")
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Valor IVA")
    
    # Total de la línea
    total = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Total")
    
    # Cuenta contable asociada
    account = models.ForeignKey(
        Account,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='document_lines',
        verbose_name="Cuenta Contable"
    )
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True, verbose_name="Metadatos")

    class Meta:
        verbose_name = "Línea de Documento"
        verbose_name_plural = "Líneas de Documentos"
        ordering = ['document', 'line_number']

    def __str__(self):
        return f"{self.document.full_number} - Línea {self.line_number}"


class DIANResolution(models.Model):
    """
    Resolución de Facturación DIAN.
    """
    # Información de la resolución
    resolution_number = models.CharField(max_length=50, unique=True, verbose_name="Número de Resolución")
    resolution_date = models.DateField(verbose_name="Fecha de Resolución")
    
    # Rango de numeración
    prefix = models.CharField(max_length=10, blank=True, verbose_name="Prefijo")
    start_number = models.IntegerField(verbose_name="Desde")
    end_number = models.IntegerField(verbose_name="Hasta")
    current_number = models.IntegerField(verbose_name="Número Actual")
    
    # Vigencia
    valid_from = models.DateField(verbose_name="Válida Desde")
    valid_to = models.DateField(verbose_name="Válida Hasta")
    
    # Configuración técnica
    technical_key = models.CharField(max_length=255, blank=True, verbose_name="Clave Técnica")
    test_set_id = models.CharField(max_length=100, blank=True, verbose_name="Test Set ID")
    
    # Estado
    is_active = models.BooleanField(default=True, verbose_name="Activa")
    is_test = models.BooleanField(default=False, verbose_name="Es de Prueba")
    
    # Notas
    notes = models.TextField(blank=True, verbose_name="Notas")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Resolución DIAN"
        verbose_name_plural = "Resoluciones DIAN"
        ordering = ['-resolution_date']

    def __str__(self):
        return f"Resolución {self.resolution_number} - {self.prefix}"
    
    def get_next_number(self):
        """Obtiene el siguiente número disponible."""
        if self.current_number >= self.end_number:
            raise ValueError("Se ha alcanzado el límite de la resolución")
        
        self.current_number += 1
        self.save()
        return self.current_number
    
    def get_available_numbers(self):
        """Retorna la cantidad de números disponibles."""
        return self.end_number - self.current_number


class DIANLog(models.Model):
    """
    Log de transacciones con la DIAN.
    """
    ACTION_CHOICES = [
        ('SEND', 'Envío'),
        ('QUERY', 'Consulta'),
        ('CANCEL', 'Anulación'),
        ('VALIDATE', 'Validación'),
    ]
    
    STATUS_CHOICES = [
        ('SUCCESS', 'Exitoso'),
        ('ERROR', 'Error'),
        ('PENDING', 'Pendiente'),
    ]
    
    # Información del log
    document = models.ForeignKey(
        ElectronicDocument,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='dian_logs',
        verbose_name="Documento"
    )
    
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name="Acción")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, verbose_name="Estado")
    
    # Request y Response
    request_data = models.JSONField(verbose_name="Datos de Solicitud")
    response_data = models.JSONField(null=True, blank=True, verbose_name="Datos de Respuesta")
    
    # Mensajes
    message = models.TextField(blank=True, verbose_name="Mensaje")
    error_message = models.TextField(blank=True, verbose_name="Mensaje de Error")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Usuario
    user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='dian_logs',
        verbose_name="Usuario"
    )

    class Meta:
        verbose_name = "Log DIAN"
        verbose_name_plural = "Logs DIAN"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_action_display()} - {self.created_at}"


class TaxType(models.Model):
    """
    Tipos de impuestos (IVA, Retención, etc.)
    """
    code = models.CharField(max_length=10, unique=True, verbose_name="Código")
    name = models.CharField(max_length=100, verbose_name="Nombre")
    description = models.TextField(blank=True, verbose_name="Descripción")
    
    TAX_CATEGORY_CHOICES = [
        ('IVA', 'IVA'),
        ('INC', 'INC (Impuesto Nacional al Consumo)'),
        ('RETEFUENTE', 'Retención en la Fuente'),
        ('RETEIVA', 'Retención de IVA'),
        ('RETEICA', 'Retención de ICA'),
    ]
    category = models.CharField(max_length=20, choices=TAX_CATEGORY_CHOICES, verbose_name="Categoría")
    
    # Tasa por defecto
    default_rate = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Tasa por Defecto (%)")
    
    # Cuenta contable asociada
    account = models.ForeignKey(
        Account,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='tax_types',
        verbose_name="Cuenta Contable"
    )
    
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Tipo de Impuesto"
        verbose_name_plural = "Tipos de Impuestos"
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"


class ElectronicDocumentTax(models.Model):
    """
    Impuestos aplicados a un documento electrónico.
    """
    document = models.ForeignKey(
        ElectronicDocument,
        on_delete=models.CASCADE,
        related_name='taxes',
        verbose_name="Documento"
    )
    
    line = models.ForeignKey(
        ElectronicDocumentLine,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='taxes',
        verbose_name="Línea"
    )
    
    tax_type = models.ForeignKey(TaxType, on_delete=models.PROTECT, verbose_name="Tipo de Impuesto")
    
    # Base gravable
    taxable_amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Base Gravable")
    
    # Tasa y valor
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Tasa (%)")
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Valor")
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Impuesto de Documento"
        verbose_name_plural = "Impuestos de Documentos"

    def __str__(self):
        return f"{self.document.full_number} - {self.tax_type.name}"
