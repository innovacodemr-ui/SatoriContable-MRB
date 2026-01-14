from django.db import models
from apps.accounting.models import ThirdParty, CostCenter
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Q
from decimal import Decimal
from datetime import date
import os
# No importamos utils aquí arriba para evitar circular imports si utils creciera, 
# pero como utils es pura logic, podemos importar dentro del método o arriba.
# Arriba es mejor.
try:
    from .utils import calculate_commercial_days
except ImportError:
    # Fallback por si migraciones corren sin el archivo listo
    calculate_commercial_days = None


def novelty_file_path(instance, filename):
    """
    Genera ruta dinámica: novelties/YYYY/MM/EMP_ID/filename
    """
    year = instance.start_date.year
    month = instance.start_date.month
    # Aseguramos que el nombre limpio se conserve
    return f'novelties/{year}/{month:02d}/EMP_{instance.employee.code}/{filename}'

# --- NEW: Modelos de Configuración y Maestros (Refactor Flexibilidad) ---

class LegalParameter(models.Model):
    """
    Almacena variables de ley (SMMLV, Auxilio Transporte, Jornada Máxima, UVT)
    con sus fechas de vigencia. Reemplaza al modelo rígido PayrollSettings.
    """
    KEYS = (
        ('SMMLV', 'Salario Mínimo Legal Vigente'),
        ('AUX_TRANS', 'Auxilio de Transporte'),
        ('MAX_WEEKLY_HOURS', 'Jornada Máxima Semanal'),
        ('UVT', 'Unidad de Valor Tributario'),
        ('SURCHARGE_DOMINICAL', 'Recargo Dominical/Festivo'),
    )

    key = models.CharField(max_length=50, choices=KEYS, db_index=True)
    value = models.DecimalField(max_digits=12, decimal_places=2, help_text="Valor monetario o numérico")
    valid_from = models.DateField(help_text="Fecha de inicio de la vigencia")
    valid_to = models.DateField(null=True, blank=True, help_text="Fecha fin (Dejar vacío si es vigente indefinidamente)")

    class Meta:
        ordering = ['-valid_from']
        verbose_name = "Parámetro Legal"
        verbose_name_plural = "Parámetros Legales"

    def __str__(self):
        return f"{self.get_key_display()} - {self.valid_from}"

    @classmethod
    def get_value(cls, key_code, query_date=None):
        """
        Método estático para obtener el valor de un parámetro en una fecha específica.
        Si no se da fecha, usa hoy.
        """
        if query_date is None:
            query_date = date.today()

        # Busca el parámetro que inició antes de la fecha y (no ha terminado O termina después de la fecha)
        param = cls.objects.filter(
            key=key_code,
            valid_from__lte=query_date
        ).filter(
            Q(valid_to__gte=query_date) | Q(valid_to__isnull=True)
        ).first()

        if not param:
            # Fallback values for 2026/2025 to avoid crashing on empty DB during dev
            if key_code == 'SMMLV': return Decimal('1300000.00')
            if key_code == 'AUX_TRANS': return Decimal('140606.00')
            if key_code == 'MAX_WEEKLY_HOURS': return Decimal('46.00')
            if key_code == 'UVT': return Decimal('47065.00')
            return Decimal('0')
        
        return param.value


class NoveltyType(models.Model):
    """
    Catálogo de tipos de novedades (Incapacidad General, Licencia Maternidad, LNR, etc.)
    Alineado con los códigos de la DIAN.
    """
    DIAN_CODE_CHOICES = (
        ('LNR', 'Licencia No Remunerada'),
        ('IGE', 'Incapacidad General'),
        ('LMA', 'Licencia Maternidad/Paternidad'),
        ('VAC', 'Vacaciones'),
        ('IRL', 'Incapacidad Laboral (ARL)'),
        ('OTR', 'Otra Novedad'),
    )

    code = models.CharField(max_length=10, db_index=True, unique=True, verbose_name="Código Interno") # Ej: IGE_66
    name = models.CharField(max_length=100, verbose_name="Nombre Novedad") # Ej: Incap. General (>2 días)
    dian_type = models.CharField(max_length=3, choices=DIAN_CODE_CHOICES, verbose_name="Tipo DIAN")
    
    # FACTORES DE PAGO
    payroll_payment_percentage = models.DecimalField(
        max_digits=5, decimal_places=4, default=0.0000,
        help_text="Porcentaje del salario que recibe el empleado (Ej: 0.6667 para el 66.67%)",
        verbose_name="% Pago Nómina"
    )
    
    # IMPACTO EN SEGURIDAD SOCIAL (Fundamental para la PILA)
    affects_transport_aid = models.BooleanField(default=True, help_text="Si es True, NO se paga auxilio de transporte esos días", verbose_name="Afecta Aux. Trans")
    pays_health = models.BooleanField(default=True, help_text="¿Se cotiza salud?", verbose_name="Cotiza Salud")
    pays_pension = models.BooleanField(default=True, help_text="¿Se cotiza pensión?", verbose_name="Cotiza Pensión")
    pays_arl = models.BooleanField(default=False, help_text="¿Se cotiza ARL?", verbose_name="Cotiza ARL")

    class Meta:
        verbose_name = "Tipo de Novedad"
        verbose_name_plural = "Tipos de Novedades"
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Employee(models.Model):
    """
    Empleado extiende un Tercero (ThirdParty) con datos específicos de contratación.
    """
    third_party = models.OneToOneField(ThirdParty, on_delete=models.CASCADE, related_name='employee_profile', verbose_name="Tercero")
    code = models.CharField(max_length=20, unique=True, verbose_name="Código Empleado")
    
    # Datos de Contratación
    CONTRACT_TYPES = [
        ('FIJO', 'Término Fijo'),
        ('INDEFINIDO', 'Término Indefinido'),
        ('OBRA', 'Obra o Labor'),
        ('APRENDIZAJE', 'Aprendizaje'),
    ]
    contract_type = models.CharField(max_length=20, choices=CONTRACT_TYPES, verbose_name="Tipo de Contrato")
    start_date = models.DateField(verbose_name="Fecha Ingreso")
    end_date = models.DateField(null=True, blank=True, verbose_name="Fecha Retiro")
    
    base_salary = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Salario Base")
    transport_allowance_eligible = models.BooleanField(default=True, verbose_name="Aplica Aux. Transporte")
    
    # Entidades de Seguridad Social
    health_entity = models.CharField(max_length=100, verbose_name="EPS")
    pension_entity = models.CharField(max_length=100, verbose_name="Fondo Pensiones")
    severance_entity = models.CharField(max_length=100, verbose_name="Fondo Cesantías")
    arl_entity = models.CharField(max_length=100, verbose_name="ARL")
    risk_level = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="Nivel Riesgo ARL")
    
    cost_center = models.ForeignKey(CostCenter, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Centro de Costo")
    position = models.CharField(max_length=100, verbose_name="Cargo")
    
    is_active = models.BooleanField(default=True, verbose_name="Activo")

    def __str__(self):
        # return f"{self.code} - {self.third_party.name}" # Error: ThirdParty has no 'name' attr, it has first_name/surname
        return f"{self.code} - {self.third_party.first_name} {self.third_party.surname}"


class EmployeeNovelty(models.Model):
    """
    Registro de novedades aplicadas a un empleado en un rango de fechas.
    """
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='novelties', verbose_name="Empleado")
    novelty_type = models.ForeignKey(NoveltyType, on_delete=models.PROTECT, verbose_name="Tipo Novedad")
    start_date = models.DateField(verbose_name="Fecha Inicio")
    end_date = models.DateField(verbose_name="Fecha Fin")
    days = models.PositiveIntegerField(help_text="Días a reportar en nómina", verbose_name="Días")
    
    # Campo para guardar el valor calculado y no recalcular siempre
    total_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Valor Total")
    
    # Opcional: Link al archivo médico
    attachment = models.FileField(upload_to=novelty_file_path, null=True, blank=True, verbose_name="Soporte")

    class Meta:
        verbose_name = "Novedad Empleado"
        verbose_name_plural = "Novedades Empleados"

    def save(self, *args, **kwargs):
        # Lógica para calcular días usando mes comercial (30 días)
        if not self.days and self.end_date and self.start_date:
             if calculate_commercial_days:
                self.days = calculate_commercial_days(self.start_date, self.end_date)
             else:
                delta = self.end_date - self.start_date
                self.days = delta.days + 1
        super().save(*args, **kwargs)


class PayrollConcept(models.Model):
    TYPES = [('EARNING', 'Devengado'), ('DEDUCTION', 'Deducción')]
    
    code = models.CharField(max_length=50, unique=True, verbose_name="Código Interno")
    name = models.CharField(max_length=200, verbose_name="Nombre Concepto")
    concept_type = models.CharField(max_length=20, choices=TYPES, verbose_name="Tipo")
    dian_code = models.CharField(max_length=50, verbose_name="Código DIAN")
    
    is_salary = models.BooleanField(default=False, verbose_name="Es Salario (Base Prestacional)")
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Porcentaje de cálculo si aplica (Ej: 25.00 para HED)")
    
    class Meta:
        verbose_name = "Concepto de Nómina"
        verbose_name_plural = "Conceptos de Nómina"

    def __str__(self):
        return f"{self.code} - {self.name}"

class PayrollPeriod(models.Model):
    """Periodo de Liquidación (Mensual/Quincenal)"""
    name = models.CharField(max_length=100, verbose_name="Nombre Periodo") # Ej: Enero 2026 - Quincena 1
    start_date = models.DateField(verbose_name="Fecha Inicio")
    end_date = models.DateField(verbose_name="Fecha Fin")
    payment_date = models.DateField(verbose_name="Fecha Pago")
    
    STATUS_CHOICES = [
        ('DRAFT', 'Borrador'),
        ('LIQUIDATED', 'Liquidado'),
        ('PAID', 'Pagado'),
        ('REPORTED', 'Transmitido DIAN'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT', verbose_name="Estado")

    def __str__(self):
        return self.name


# --- Nómina Electrónica (Estructura XML DIAN) ---

class PayrollDocument(models.Model):
    """
    Documento Soporte de Pago de Nómina Electrónica (Por empleado y periodo)
    Equivalente al encabezado del XML.
    """
    period = models.ForeignKey(PayrollPeriod, on_delete=models.PROTECT, related_name='documents')
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name='payroll_documents')
    
    # Identificadores DIAN
    cune = models.CharField(max_length=255, null=True, blank=True, unique=True, verbose_name="CUNE")
    conseccutive = models.IntegerField(verbose_name="Consecutivo")
    prefix = models.CharField(max_length=10, blank=True, verbose_name="Prefijo")
    
    # Totales Calculados
    worked_days = models.IntegerField(default=30, verbose_name="Días Trabajados")
    novelty_days = models.IntegerField(default=0, verbose_name="Días Novedad")
    accrued_total = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Total Devengado")
    deductions_total = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Total Deducciones")
    net_total = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Neto a Pagar")

    # Estados
    xml_file = models.FileField(upload_to='payroll_xmls/', null=True, blank=True)
    dian_status = models.CharField(max_length=20, default='PENDING', verbose_name="Estado DIAN")
    # PENDING, SENT, ACCEPTED, REJECTED
    dian_response = models.TextField(blank=True, null=True, verbose_name="Respuesta DIAN")
    
    class Meta:
        unique_together = ('period', 'employee')


class PayrollDetail(models.Model):
    """
    Detalle de conceptos (Devengados y Deducciones)
    Cada fila representa una línea del XML (Basic, Transporte, HED, HEN, Salud, etc)
    """
    document = models.ForeignKey(PayrollDocument, on_delete=models.CASCADE, related_name='details')
    
    CONCEPT_TYPES = [
        ('EARNING', 'Devengado'),
        ('DEDUCTION', 'Deducción'),
    ]
    concept_type = models.CharField(max_length=20, choices=CONCEPT_TYPES)
    
    # Códigos DIAN Estándar (Res 000013)
    # Ej: BASICO, TRANSPORTE, HED, HEN, HRN, HEDDF, HRDDF, OTRA_NOV
    dian_code = models.CharField(max_length=50, verbose_name="Código DIAN") 
    description = models.CharField(max_length=200, verbose_name="Descripción")
    
    quantity = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name="Cantidad (Horas/Días)")
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Porcentaje")
    value = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor")

    class Meta:
        verbose_name = "Detalle de Nómina"
    
    def __str__(self):
        return f"{self.document.employee.code} - {self.description}: {self.value}"
