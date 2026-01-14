from django.db import models
from django.conf import settings
from apps.tenants.models import Client

class ClientDomain(models.Model):
    """
    Dominios de correo autorizados para JIT Provisioning.
    Ej: @ab11.com.co -> Auto-unirse al Tenant AB 11
    """
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='domains', null=True, blank=True)
    domain = models.CharField(max_length=255, unique=True, verbose_name="Dominio (ej: empresa.com)", null=True, blank=True)
    
    # created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f"@{self.domain} -> {self.client.name if self.client else 'Sin Cliente'}"


class Invitation(models.Model):
    """
    Invitaciones para usuarios colaboradores.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pendiente'),
        ('ACCEPTED', 'Aceptada'),
        ('EXPIRED', 'Expirada'),
    ]
    
    ROLE_CHOICES = [
        ('ADMIN', 'Administrador de Tenant'),
        ('CONTADOR', 'Contador'),
        ('AUXILIAR', 'Auxiliar Contable'),
        ('VENDEDOR', 'Vendedor'),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='invitations', null=True, blank=True)
    email = models.EmailField(verbose_name="Correo Electrónico", null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='AUXILIAR')
    token = models.CharField(max_length=64, unique=True, verbose_name="Token de Invitación", null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', verbose_name="Estado")
    expires_at = models.DateTimeField(verbose_name="Fecha de Expiración", null=True, blank=True)
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='sent_invitations')
    # created_at = models.DateTimeField(auto_now_add=True, null=True)
    accepted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Invitación a {self.email or 'N/A'}"
    
    class Meta:
        unique_together = ('client', 'email')