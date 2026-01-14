from django.db import models
# from django_tenants.models import TenantMixin, DomainMixin
from django.conf import settings

# Para MVP Single Tenant, usamos models.Model
class Client(models.Model):
    """
    Modelo de Cliente/Empresa.
    En MVP es unico, en futuro será TenantMixin.
    """
    name = models.CharField(max_length=200, verbose_name="Nombre de la Empresa")
    nit = models.CharField(max_length=20, unique=True, verbose_name="NIT")
    
    # Información de la empresa
    legal_name = models.CharField(max_length=300, verbose_name="Razón Social")
    business_name = models.CharField(max_length=200, blank=True, verbose_name="Nombre Comercial")
    
    # Tipo de régimen
    TAX_REGIME_CHOICES = [
        ('COMUN', 'Régimen Común'),
        ('SIMPLIFICADO', 'Régimen Simplificado'),
        ('ESPECIAL', 'Régimen Especial'),
    ]
    tax_regime = models.CharField(
        max_length=20,
        choices=TAX_REGIME_CHOICES,
        default='COMUN',
        verbose_name="Régimen Tributario"
    )
    
    # Responsabilidades fiscales
    fiscal_responsibilities = models.JSONField(
        default=list,
        verbose_name="Responsabilidades Fiscales",
        help_text="Códigos de responsabilidades fiscales según DIAN"
    )
    
    # Ubicación
    address = models.TextField(verbose_name="Dirección")
    city = models.CharField(max_length=100, default='Cali', verbose_name="Ciudad")
    department = models.CharField(max_length=100, default='Valle del Cauca', verbose_name="Departamento")
    country = models.CharField(max_length=100, default='Colombia', verbose_name="País")
    postal_code = models.CharField(max_length=20, blank=True, verbose_name="Código Postal")
    
    # Contacto
    phone = models.CharField(max_length=50, verbose_name="Teléfono")
    email = models.EmailField(verbose_name="Email")
    website = models.URLField(blank=True, verbose_name="Sitio Web")
    
    # DIAN Configuration
    dian_software_id = models.CharField(max_length=100, blank=True, verbose_name="ID Software DIAN")
    dian_test_set_id = models.CharField(max_length=100, blank=True, verbose_name="Test Set ID DIAN")
    
    # --- Firma Digital y Marca (Onboarding) ---
    dian_certificate = models.FileField(
        upload_to='dian_certificates/',
        blank=True,
        null=True,
        verbose_name="Certificado Digital .p12"
    )
    # Almacenamos la contraseña cifrada (base64 del encrypted bytes)
    certificate_password_encrypted = models.CharField(
        max_length=500, 
        blank=True, 
        verbose_name="Contraseña Certificado (Cifrada)"
    )
    # Campo legacy: mantener por compatibilidad temporal o eliminar. 
    # Lo dejamos blank pero la UI no lo usará.
    dian_certificate_password = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name="Contraseña Certificado (Legacy - No usar)"
    )

    logo = models.ImageField(
        upload_to='company_logos/',
        blank=True,
        null=True,
        verbose_name="Logo Empresa"
    )
    
    # Plan de pago
    PLAN_CHOICES = [
        ('FREE', 'Gratuito'),
        ('BASIC', 'Básico'),
        ('PROFESSIONAL', 'Profesional'),
        ('ENTERPRISE', 'Empresarial'),
    ]
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='FREE', verbose_name="Plan")
    
    # Estado
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_on = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    modified_on = models.DateTimeField(auto_now=True, verbose_name="Última Modificación")
    
    # Configuración de sincronización
    sync_enabled = models.BooleanField(default=True, verbose_name="Sincronización Habilitada")
    last_sync = models.DateTimeField(null=True, blank=True, verbose_name="Última Sincronización")
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True, verbose_name="Metadatos")
    
    # Campo para JIT Provisioning (Dominios permitidos)
    # domains = related_name from ClientDomain

    def __str__(self):
        return f"{self.name} ({self.nit})"


    class Meta:
        verbose_name = "Cliente/Empresa"
        verbose_name_plural = "Clientes/Empresas"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.nit}"

    auto_create_schema = True


# class Domain(DomainMixin):
#     """
#     Modelo de Dominio para Multi-tenancy.
#     Cada cliente puede tener múltiples dominios.
#     """
#     pass
