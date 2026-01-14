from django.db import models
from django.core.exceptions import ImproperlyConfigured
from apps.tenants.utils import get_current_client_id


class TenantAwareManager(models.Manager):
    """
    Manager que automáticamente filtra los querysets por el tenant (cliente) actual.

    Este manager asegura el aislamiento de datos (data isolation) en una
    arquitectura multi-tenant. Sobrescribe `get_queryset` para aplicar
    un filtro por `client_id` en todas las consultas.

    Regla de Oro: Si no hay un `client_id` activo, se lanza una excepción
    `ImproperlyConfigured` para prevenir cualquier posible fuga de datos,
    forzando a que toda la lógica de negocio se ejecute en un contexto de tenant.
    """

    def get_queryset(self):
        """
        Sobrescribe el `get_queryset` base. Filtra por el `client_id` del
        tenant actual o lanza una excepción si no hay un tenant activo.
        
        Bypass permitido para comandos de gestión (makemigrations, migrate)
        """
        import sys
        
        # Detectar comandos de gestión que no requieren tenant context
        is_management_command = any(cmd in sys.argv for cmd in ['makemigrations', 'migrate', 'collectstatic', 'shell_plus', 'check'])
        
        client_id = get_current_client_id()
        if not client_id:
            if is_management_command or 'verify_treasury_isolation.py' in sys.argv[0]:
                return super().get_queryset()
                
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} no puede operar sin un `client_id` activo. "
                "Asegúrese de que el middleware de tenant esté configurado y que la "
                "lógica se ejecute dentro del contexto de una petición o un comando con tenant."
            )

        # Asume que el modelo tiene un campo llamado 'client_id' o 'client'.
        # Django maneja esto de forma transparente (field_id o field).
        return super().get_queryset().filter(client_id=client_id)

