from django.db import models
from django.contrib.auth.models import User


class SyncLog(models.Model):
    """
    Registro de sincronización entre aplicación de escritorio y servidor.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pendiente'),
        ('IN_PROGRESS', 'En Progreso'),
        ('COMPLETED', 'Completado'),
        ('FAILED', 'Fallido'),
    ]
    
    client_id = models.CharField(max_length=100, verbose_name="ID del Cliente")
    sync_type = models.CharField(max_length=50, verbose_name="Tipo de Sincronización")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    records_sent = models.IntegerField(default=0, verbose_name="Registros Enviados")
    records_received = models.IntegerField(default=0, verbose_name="Registros Recibidos")
    records_failed = models.IntegerField(default=0, verbose_name="Registros Fallidos")
    
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    error_message = models.TextField(blank=True)
    sync_data = models.JSONField(default=dict, blank=True)
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Log de Sincronización"
        verbose_name_plural = "Logs de Sincronización"
        ordering = ['-created_at']

    def __str__(self):
        return f"Sync {self.client_id} - {self.created_at}"
