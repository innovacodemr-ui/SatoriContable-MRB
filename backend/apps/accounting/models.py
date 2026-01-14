from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
import hashlib

from apps.common.managers import TenantAwareManager


class AccountClass(models.Model):
    """
    Clase de Cuenta (Nivel 1 del PUC).
    Ejemplos: 1-Activo, 2-Pasivo, 3-Patrimonio, 4-Ingresos, 5-Gastos, 6-Costos
    """
    client = models.ForeignKey('tenants.Client', on_delete=models.CASCADE)
    code = models.CharField(max_length=1, verbose_name="Código")
    name = models.CharField(max_length=100, verbose_name="Nombre")
    description = models.TextField(blank=True, verbose_name="Descripción")

    NATURE_CHOICES = [
        ('DEBITO', 'Débito'),
        ('CREDITO', 'Crédito'),
    ]
    nature = models.CharField(max_length=10, choices=NATURE_CHOICES, verbose_name="Naturaleza")

    is_active = models.BooleanField(default=True, verbose_name="Activa")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantAwareManager()

    class Meta:
        verbose_name = "Clase de Cuenta"
        verbose_name_plural = "Clases de Cuentas"
        ordering = ['code']
        unique_together = ('client', 'code')

    def __str__(self):
        return f"{self.code} - {self.name}"


class AccountGroup(models.Model):
    """
    Grupo de Cuenta (Nivel 2 del PUC).
    Ejemplo: 11-Disponible, 12-Inversiones, 13-Deudores
    """
    client = models.ForeignKey('tenants.Client', on_delete=models.CASCADE)
    account_class = models.ForeignKey(AccountClass, on_delete=models.CASCADE, related_name='groups')
    code = models.CharField(max_length=2, verbose_name="Código")
    name = models.CharField(max_length=150, verbose_name="Nombre")
    description = models.TextField(blank=True, verbose_name="Descripción")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantAwareManager()

    class Meta:
        verbose_name = "Grupo de Cuenta"
        verbose_name_plural = "Grupos de Cuentas"
        ordering = ['code']
        unique_together = ('client', 'code')

    def __str__(self):
        return f"{self.code} - {self.name}"


class DianFormat(models.Model):
    """
    Formatos para Reporte de Información Exógena (Medios Magnéticos) DIAN.
    Ejemplo: Formato 1001 - Pagos o abonos en cuenta y retenciones.
    """
    code = models.CharField(max_length=10, verbose_name="Código Formato")
    name = models.CharField(max_length=255, verbose_name="Nombre del Formato")
    version = models.IntegerField(default=1, verbose_name="Versión")
    valid_from = models.IntegerField(verbose_name="Año Vigencia") # Ej: 2025

    class Meta:
        verbose_name = "Formato DIAN"
        verbose_name_plural = "Formatos DIAN (Exógena)"
        unique_together = ('code', 'version', 'valid_from')
        ordering = ['code', 'version']

    def __str__(self):
        return f"Formato {self.code} v{self.version} - {self.name}"


class DianConcept(models.Model):
    """
    Conceptos asociados a un Formato DIAN.
    Ejemplo: 5001 - Salarios y demás pagos laborales (para el Formato 1001).
    """
    format = models.ForeignKey(DianFormat, on_delete=models.CASCADE, related_name='concepts', verbose_name="Formato")
    code = models.CharField(max_length=10, verbose_name="Código Concepto")
    name = models.CharField(max_length=500, verbose_name="Nombre del Concepto")
    description = models.TextField(blank=True, verbose_name="Descripción")

    class Meta:
        verbose_name = "Concepto DIAN"
        verbose_name_plural = "Conceptos DIAN"
        unique_together = ('format', 'code')
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"


class Account(models.Model):
    """
    Cuenta Contable (Nivel 3-6 del PUC).
    Manejo completo del Plan Único de Cuentas colombiano.
    """
    client = models.ForeignKey('tenants.Client', on_delete=models.CASCADE)
    account_group = models.ForeignKey(AccountGroup, on_delete=models.CASCADE, related_name='accounts')

    # Código completo de la cuenta (puede tener hasta 10 dígitos)
    code = models.CharField(max_length=20, verbose_name="Código")
    name = models.CharField(max_length=250, verbose_name="Nombre")
    description = models.TextField(blank=True, verbose_name="Descripción")

    # Nivel de la cuenta en el PUC (3, 4, 5, 6)
    level = models.IntegerField(verbose_name="Nivel")

    # Cuenta padre (para cuentas de nivel > 3)
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='children',
        verbose_name="Cuenta Padre"
    )

    # Naturaleza de la cuenta
    NATURE_CHOICES = [
        ('DEBITO', 'Débito'),
        ('CREDITO', 'Crédito'),
    ]
    nature = models.CharField(max_length=10, choices=NATURE_CHOICES, verbose_name="Naturaleza")

    # Tipos de cuenta
    ACCOUNT_TYPE_CHOICES = [
        ('ACTIVO', 'Activo'),
        ('PASIVO', 'Pasivo'),
        ('PATRIMONIO', 'Patrimonio'),
        ('INGRESO', 'Ingreso'),
        ('GASTO', 'Gasto'),
        ('COSTO', 'Costo de Ventas'),
    ]
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES, verbose_name="Tipo de Cuenta")

    # Indica si la cuenta permite movimientos directos
    allows_movement = models.BooleanField(default=True, verbose_name="Permite Movimientos")

    # Indica si requiere tercero
    requires_third_party = models.BooleanField(default=False, verbose_name="Requiere Tercero")

    # Indica si requiere centro de costo
    requires_cost_center = models.BooleanField(default=False, verbose_name="Requiere Centro de Costo")

    # Indica si maneja base de retención
    manages_retention = models.BooleanField(default=False, verbose_name="Maneja Retención")

    # Configuración para impuestos
    is_tax_account = models.BooleanField(default=False, verbose_name="Cuenta de Impuestos")
    tax_type = models.CharField(
        max_length=50,
        blank=True,
        choices=[
            ('IVA', 'IVA'),
            ('RETEFUENTE', 'Retención en la Fuente'),
            ('RETEIVA', 'Retención de IVA'),
            ('RETEICA', 'Retención de ICA'),
            ('CREE', 'CREE'),
        ],
        verbose_name="Tipo de Impuesto"
    )

    # Estado
    is_active = models.BooleanField(default=True, verbose_name="Activa")

    # Configuración Medios Magnéticos (Exógena) - MOVIDO A MODELO AccountDianConfiguration
    # dian_format = models.ForeignKey(...)
    # dian_concept = models.ForeignKey(...)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='accounts_created',
        verbose_name="Creado por"
    )

    objects = TenantAwareManager()

    class Meta:
        verbose_name = "Cuenta Contable"
        verbose_name_plural = "Cuentas Contables"
        ordering = ['code']
        unique_together = ('client', 'code')
        indexes = [
            models.Index(fields=['client', 'code']),
            models.Index(fields=['account_type']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def get_balance(self):
        """Calcula el saldo actual de la cuenta."""
        from django.db.models import Sum, Q

        debits = self.journal_entry_lines.filter(
            entry__status='POSTED'
        ).aggregate(total=Sum('debit'))['total'] or Decimal('0')

        credits = self.journal_entry_lines.filter(
            entry__status='POSTED'
        ).aggregate(total=Sum('credit'))['total'] or Decimal('0')

        if self.nature == 'DEBITO':
            return debits - credits
        else:
            return credits - debits

    def get_full_path(self):
        """Retorna la ruta completa de la cuenta."""
        if self.parent:
            return f"{self.parent.get_full_path()} > {self.name}"
        return f"{self.account_group.account_class.name} > {self.account_group.name} > {self.name}"



class AccountDianConfiguration(models.Model):
    """
    Configuración de Medios Magnéticos por Cuenta.
    Permite asociar una cuenta a múltiples formatos/conceptos (hasta 5 según req).
    """
    client = models.ForeignKey('tenants.Client', on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='dian_configurations')
    dian_format = models.ForeignKey(DianFormat, on_delete=models.CASCADE, verbose_name="Formato")
    dian_concept = models.ForeignKey(DianConcept, on_delete=models.CASCADE, verbose_name="Concepto")

    objects = TenantAwareManager()

    class Meta:
        verbose_name = "Configuración DIAN de Cuenta"
        verbose_name_plural = "Configuraciones DIAN de Cuentas"
        unique_together = ('client', 'account', 'dian_format', 'dian_concept')


class CostCenter(models.Model):
    """
    Centro de Costo para el sistema contable.
    """
    client = models.ForeignKey('tenants.Client', on_delete=models.CASCADE)
    code = models.CharField(max_length=20, verbose_name="Código")
    name = models.CharField(max_length=200, verbose_name="Nombre")
    description = models.TextField(blank=True, verbose_name="Descripción")

    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='children',
        verbose_name="Centro de Costo Padre"
    )

    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantAwareManager()

    class Meta:
        verbose_name = "Centro de Costo"
        verbose_name_plural = "Centros de Costo"
        ordering = ['code']
        unique_together = ('client', 'code')

    def __str__(self):
        return f"{self.code} - {self.name}"


class ThirdParty(models.Model):
    """
    Terceros (Clientes, Proveedores, Empleados, etc.)
    Cumple con requisitos DIAN para Facturación Electrónica (Anexo Técnico 1.8/1.9)
    """
    client = models.ForeignKey('tenants.Client', on_delete=models.CASCADE)
    PARTY_TYPE_CHOICES = [
        ('CLIENTE', 'Cliente'),
        ('PROVEEDOR', 'Proveedor'),
        ('EMPLEADO', 'Empleado'),
        ('SOCIO', 'Socio'),
        ('OTRO', 'Otro'),
    ]

    PERSON_TYPE_CHOICES = [
        (1, 'Persona Jurídica'),
        (2, 'Persona Natural'),
    ]

    # ========== IDENTIFICACIÓN (Core) ==========
    party_type = models.CharField(max_length=20, choices=PARTY_TYPE_CHOICES, verbose_name="Tipo de Tercero")
    person_type = models.IntegerField(choices=PERSON_TYPE_CHOICES, verbose_name="Tipo de Persona")

    # Códigos DIAN oficiales para Facturación Electrónica
    IDENTIFICATION_TYPE_CHOICES = [
        ('11', 'Registro civil'),
        ('12', 'Tarjeta de identidad'),
        ('13', 'Cédula de ciudadanía'),
        ('21', 'Tarjeta de extranjería'),
        ('22', 'Cédula de extranjería'),
        ('31', 'NIT'),
        ('41', 'Pasaporte'),
        ('42', 'Documento de identificación extranjero'),
        ('47', 'PEP - Permiso Especial de Permanencia'),
        ('50', 'NIT de otro país'),
        ('91', 'NUIP'),
    ]
    identification_type = models.CharField(
        max_length=2,
        choices=IDENTIFICATION_TYPE_CHOICES,
        verbose_name="Tipo de Identificación DIAN"
    )
    identification_number = models.CharField(
        max_length=20,
        verbose_name="Número de Identificación"
    )
    identification_number_hash = models.CharField(
        max_length=64, 
        blank=True, 
        verbose_name="Hash del Número de Identificación"
    )
    check_digit = models.CharField(
        max_length=1,
        blank=True,
        verbose_name="Dígito de Verificación (DV)",
        help_text="Obligatorio para NIT (31) - Calculado con Módulo 11"
    )

    # ========== NOMBRES Y RAZÓN SOCIAL ==========
    # Para Persona Jurídica
    business_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Razón Social",
        help_text="Obligatorio si es Persona Jurídica"
    )
    trade_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Nombre Comercial",
        help_text="Opcional - Nombre con el que se conoce comercialmente"
    )

    # Para Persona Natural - DIAN exige nombres y apellidos separados
    first_name = models.CharField(
        max_length=60,
        blank=True,
        verbose_name="Primer Nombre",
        help_text="Obligatorio si es Persona Natural"
    )
    middle_name = models.CharField(
        max_length=60,
        blank=True,
        verbose_name="Segundo Nombre"
    )
    surname = models.CharField(
        max_length=60,
        blank=True,
        verbose_name="Primer Apellido",
        help_text="Obligatorio si es Persona Natural"
    )
    second_surname = models.CharField(
        max_length=60,
        blank=True,
        verbose_name="Segundo Apellido"
    )

    # ========== UBICACIÓN GEOGRÁFICA (DANE y Código Postal) ==========
    country_code = models.CharField(
        max_length=2,
        default='CO',
        verbose_name="Código País (ISO 3166-1)",
        help_text="CO para Colombia"
    )
    department_code = models.CharField(
        max_length=2,
        verbose_name="Código DANE Departamento",
        help_text="Ej: 76=Valle, 11=Bogotá, 05=Antioquia"
    )
    city_code = models.CharField(
        max_length=5,
        verbose_name="Código DANE Municipio",
        help_text="Ej: 76001=Cali, 11001=Bogotá, 05001=Medellín"
    )
    postal_code = models.CharField(
        max_length=10,
        verbose_name="Código Postal",
        help_text="Obligatorio para Facturación Electrónica - 6 dígitos en Colombia"
    )
    address = models.TextField(verbose_name="Dirección Completa")

    # ========== RESPONSABILIDADES FISCALES (Tributario) ==========
    TAX_REGIME_CHOICES = [
        ('48', 'Responsable de IVA (Antes Régimen Común)'),
        ('49', 'No Responsable de IVA (Antes Régimen Simplificado)'),
        ('42', 'Régimen Simple de Tributación'),
    ]
    tax_regime = models.CharField(
        max_length=2,
        choices=TAX_REGIME_CHOICES,
        default='49',
        verbose_name="Régimen Tributario DIAN"
    )

    # Responsabilidades fiscales (RUT casilla 53)
    fiscal_responsibilities = models.JSONField(
        default=list,
        verbose_name="Responsabilidades Fiscales",
        help_text="Códigos DIAN: O-13=Gran Contribuyente, O-15=Autorretenedor, O-23=Agente Retención IVA, O-47=Régimen Simple, R-99-PN=No aplica"
    )

    ciiu_code = models.CharField(
        max_length=10,
        blank=True,
        verbose_name="Código CIIU (Actividad Económica)",
        help_text="Vital para calcular tarifa de ICA según municipio"
    )

    # ========== DATOS DE CONTACTO (Entrega de Factura) ==========
    email = models.EmailField(
        verbose_name="Email",
        help_text="Correo donde llegará el XML y PDF de la factura electrónica"
    )
    phone = models.CharField(
        max_length=50,
        verbose_name="Teléfono Principal"
    )
    mobile = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Celular"
    )

    # Información bancaria
    bank_name = models.CharField(max_length=100, blank=True, verbose_name="Banco")
    bank_account_type = models.CharField(
        max_length=20,
        blank=True,
        choices=[('AHORROS', 'Ahorros'), ('CORRIENTE', 'Corriente')],
        verbose_name="Tipo de Cuenta"
    )
    bank_account_number = models.CharField(max_length=50, blank=True, verbose_name="Número de Cuenta")

    # Configuración contable
    default_account = models.ForeignKey(
        Account,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='third_parties',
        verbose_name="Cuenta Contable Por Defecto"
    )

    # Estado
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Metadata
    notes = models.TextField(blank=True, verbose_name="Notas")

    objects = TenantAwareManager()

    class Meta:
        verbose_name = "Tercero"
        verbose_name_plural = "Terceros"
        ordering = ['business_name', 'first_name']
        unique_together = ('client', 'identification_number_hash')
        indexes = [
            models.Index(fields=['client', 'identification_number_hash']),
            models.Index(fields=['party_type']),
            models.Index(fields=['person_type']),
            models.Index(fields=['tax_regime']),
        ]

    def __str__(self):
        if self.person_type == 1:  # Persona Jurídica
            return f"{self.identification_number} - {self.business_name}"
        return f"{self.identification_number} - {self.get_full_name()}"

    def get_full_name(self):
        """Retorna el nombre completo del tercero."""
        if self.person_type == 1:  # Persona Jurídica
            return self.business_name or self.trade_name or 'Sin nombre'
        # Persona Natural - DIAN requiere nombres separados
        names = []
        if self.first_name:
            names.append(self.first_name)
        if self.middle_name:
            names.append(self.middle_name)
        if self.surname:
            names.append(self.surname)
        if self.second_surname:
            names.append(self.second_surname)
        return ' '.join(names) if names else 'Sin nombre'

    def calculate_check_digit(self):
        """
        Calcula el Dígito de Verificación para NIT usando algoritmo Módulo 11 de la DIAN.
        Solo aplica si identification_type == '31' (NIT)
        """
        if self.identification_type != '31':
            return ''

        nit = self.identification_number.strip()
        if not nit.isdigit():
            return ''

        # Algoritmo Módulo 11 DIAN
        # Pesos alineados a la derecha (NIT invertido): 3, 7, 13...
        weights = [3, 7, 13, 17, 19, 23, 29, 37, 41, 43, 47, 53, 59, 67, 71]
        total = sum(int(digit) * weight for digit, weight in zip(reversed(nit), weights))
        remainder = total % 11

        if remainder in (0, 1):
            return str(remainder)
        return str(11 - remainder)

    def save(self, *args, **kwargs):
        """Validaciones y hashing antes de guardar"""
        # Auto-calcular DV si es NIT y no está definido
        if self.identification_type == '31' and not self.check_digit:
            self.check_digit = self.calculate_check_digit()

        # Generar hash del número de identificación
        if self.identification_number:
            self.identification_number_hash = hashlib.sha256(self.identification_number.encode('utf-8')).hexdigest()

        # Validar que si es Persona Jurídica tenga business_name
        if self.person_type == 1 and not self.business_name:
            raise ValueError("Persona Jurídica debe tener Razón Social (business_name)")

        # Validar que si es Persona Natural tenga al menos primer nombre y apellido
        if self.person_type == 2 and (not self.first_name or not self.surname):
            raise ValueError("Persona Natural debe tener al menos Primer Nombre y Primer Apellido")

        super().save(*args, **kwargs)


class AccountingDocumentType(models.Model):
    """
    Tipo de Documento Contable.
    Define el tipo de documento (FV, RC, CE, etc.) y controla sus consecutivos.
    """
    client = models.ForeignKey('tenants.Client', on_delete=models.CASCADE, related_name='accounting_document_types')
    code = models.CharField(max_length=10, verbose_name="Código/Prefijo")
    name = models.CharField(max_length=100, verbose_name="Nombre")

    # Control de Consecutivos
    current_number = models.PositiveIntegerField(default=0, verbose_name="Consecutivo Actual")

    # Configuración
    is_active = models.BooleanField(default=True, verbose_name="Activo")

    objects = TenantAwareManager()

    class Meta:
        verbose_name = "Tipo de Documento Contable"
        verbose_name_plural = "Tipos de Documentos Contables"
        ordering = ['code']
        unique_together = ('client', 'code')

    def __str__(self):
        return f"{self.code} - {self.name}"


class JournalEntry(models.Model):
    """
    Comprobante Contable / Asiento Contable.
    """
    client = models.ForeignKey('tenants.Client', on_delete=models.CASCADE)
    document_type = models.ForeignKey(
        AccountingDocumentType,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='journal_entries',
        verbose_name="Tipo de Documento"
    )

    # Relación Polimórfica (GenericForeignKey)
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    ENTRY_TYPE_CHOICES = [
        ('APERTURA', 'Apertura'),
        ('DIARIO', 'Diario'),
        ('AJUSTE', 'Ajuste'),
        ('CIERRE', 'Cierre'),
        ('NOTA', 'Nota Contable'),
    ]

    STATUS_CHOICES = [
        ('DRAFT', 'Borrador'),
        ('POSTED', 'Contabilizado'),
        ('CANCELLED', 'Anulado'),
    ]

    # Información básica
    number = models.CharField(max_length=50, verbose_name="Número")
    entry_type = models.CharField(max_length=20, choices=ENTRY_TYPE_CHOICES, verbose_name="Tipo de Comprobante")
    date = models.DateField(verbose_name="Fecha")
    description = models.TextField(verbose_name="Descripción")

    # Referencias
    reference = models.CharField(max_length=100, blank=True, verbose_name="Referencia")
    external_reference = models.CharField(max_length=100, blank=True, verbose_name="Referencia Externa")

    # Estado
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT', verbose_name="Estado")

    # Usuario responsable
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='journal_entries_created',
        verbose_name="Creado por"
    )
    posted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='journal_entries_posted',
        verbose_name="Contabilizado por"
    )
    posted_at = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Contabilización")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Metadata
    notes = models.TextField(blank=True, verbose_name="Notas")
    attachments = models.JSONField(default=list, blank=True, verbose_name="Adjuntos")

    objects = TenantAwareManager()

    class Meta:
        verbose_name = "Comprobante Contable"
        verbose_name_plural = "Comprobantes Contables"
        ordering = ['-date', '-number']
        unique_together = ('client', 'number')
        indexes = [
            models.Index(fields=['client', 'date']),
            models.Index(fields=['client', 'status']),
            models.Index(fields=['client', 'entry_type']),
        ]

    def __str__(self):
        return f"{self.number} - {self.date} - {self.description[:50]}"

    def get_total_debit(self):
        """Calcula el total de débitos."""
        return self.lines.aggregate(total=Sum('debit'))['total'] or Decimal('0')

    def get_total_credit(self):
        """Calcula el total de créditos."""
        return self.lines.aggregate(total=Sum('credit'))['total'] or Decimal('0')

    def is_balanced(self):
        """Verifica si el asiento está balanceado."""
        return self.get_total_debit() == self.get_total_credit()

    def clean(self):
        super().clean()
        if self.status == 'POSTED':
            if not self.pk:
                # Si es nuevo y ya viene como POSTED (raro pero posible),
                # no podemos validar líneas aun porque no se han guardado.
                pass
            else:
                if not self.is_balanced():
                    raise ValidationError(_("El asiento contable no está balanceado. Débitos: %(debit)s, Créditos: %(credit)s") % {
                        'debit': self.get_total_debit(), 'credit': self.get_total_credit()
                    })
                if not self.lines.exists():
                    raise ValidationError("El asiento contable debe tener al menos un movimiento.")

    def save(self, *args, **kwargs):
        if self.status == 'POSTED' and not self.posted_at:
            from django.utils import timezone
            self.posted_at = timezone.now()
        super().save(*args, **kwargs)



class JournalEntryLine(models.Model):
    """
    Línea de Comprobante Contable / Movimiento Contable.
    """
    client = models.ForeignKey('tenants.Client', on_delete=models.CASCADE)
    entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='lines', verbose_name="Comprobante")
    line_number = models.IntegerField(verbose_name="Línea")

    # Cuenta contable
    account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='journal_entry_lines',
        verbose_name="Cuenta"
    )

    # Tercero (opcional)
    third_party = models.ForeignKey(
        ThirdParty,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='journal_entry_lines',
        verbose_name="Tercero"
    )

    # Centro de costo (opcional)
    cost_center = models.ForeignKey(
        CostCenter,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='journal_entry_lines',
        verbose_name="Centro de Costo"
    )

    # Movimiento
    description = models.CharField(max_length=500, verbose_name="Descripción")
    debit = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Débito")
    credit = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="Crédito")

    # Base para retenciones
    base_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name="Base"
    )

    # Metadata
    metadata = models.JSONField(default=dict, blank=True, verbose_name="Metadatos")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantAwareManager()

    class Meta:
        verbose_name = "Movimiento Contable"
        verbose_name_plural = "Movimientos Contables"
        ordering = ['entry', 'line_number']
        unique_together = ('entry', 'line_number')
        indexes = [
            models.Index(fields=['client', 'entry', 'line_number']),
            models.Index(fields=['client', 'account']),
        ]

    def __str__(self):
        return f"{self.entry.number} - Línea {self.line_number} - {self.account.code}"


class AccountingTemplate(models.Model):
    """
    Plantilla Contable para automatización de asientos.
    Define cómo contabilizar un tipo de documento.
    """
    client = models.ForeignKey('tenants.Client', on_delete=models.CASCADE)
    name = models.CharField(max_length=150, verbose_name="Nombre de Plantilla")
    document_type = models.ForeignKey(
        AccountingDocumentType,
        on_delete=models.CASCADE,
        related_name='templates',
        verbose_name="Tipo de Documento"
    )
    active = models.BooleanField(default=True, verbose_name="Activa")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantAwareManager()

    class Meta:
        verbose_name = "Plantilla Contable"
        verbose_name_plural = "Plantillas Contables"
        ordering = ['name']
        unique_together = ('client', 'name')

    def __str__(self):
        return self.name


class AccountingTemplateLine(models.Model):
    """
    Línea de configuración de una Plantilla Contable.
    """
    client = models.ForeignKey('tenants.Client', on_delete=models.CASCADE)
    NATURE_CHOICES = [
        ('DEBITO', 'Débito'),
        ('CREDITO', 'Crédito'),
    ]

    CALCULATION_METHOD_CHOICES = [
        ('FIXED_VALUE', 'Valor Fijo'),
        ('PERCENTAGE_OF_SUBTOTAL', '% del Subtotal'),
        ('PERCENTAGE_OF_TOTAL', '% del Total'),
        ('PERCENTAGE_OF_TAX', '% del Impuesto'),
        ('PLUG', 'Diferencia (Plug) / Saldo'),
    ]

    template = models.ForeignKey(AccountingTemplate, on_delete=models.CASCADE, related_name='lines', verbose_name="Plantilla")
    account = models.ForeignKey(Account, on_delete=models.PROTECT, verbose_name="Cuenta Contable")
    nature = models.CharField(max_length=10, choices=NATURE_CHOICES, verbose_name="Naturaleza")

    calculation_method = models.CharField(
        max_length=30,
        choices=CALCULATION_METHOD_CHOICES,
        verbose_name="Método de Cálculo"
    )

    value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Valor / Porcentaje",
        help_text="Si es porcentaje, usar 19.00 para 19%. Si es PLUG, dejar en 0."
    )

    description_template = models.CharField(
        max_length=255,
        verbose_name="Plantilla de Descripción",
        help_text="Variables disponibles: {numero}, {tercero}, {fecha}"
    )

    objects = TenantAwareManager()

    class Meta:
        verbose_name = "Línea de Plantilla Contable"
        verbose_name_plural = "Líneas de Plantillas Contables"
        ordering = ['id']

    def __str__(self):
        return f"{self.template.name} - {self.account.code}"