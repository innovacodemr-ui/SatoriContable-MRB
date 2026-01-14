from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from apps.tenants.models import Client
from apps.accounting.models import ThirdParty
from apps.payroll.models import Employee, CostCenter
from apps.core.models import Invitation, ClientDomain
import logging 

logger = logging.getLogger(__name__)

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Adapter custom para manejar JIT Provisioning e Invitaciones.
    Implementa 'Auto-Tenant' para ab11.com.co
    """
    def is_open_for_signup(self, request, sociallogin):
        return True
        
    def populate_user(self, request, sociallogin, data):
        """
        Hook para popular datos del usuario.
        Interceptamos aqui para asegurar que siempre haya un username valido
        y evitar la pantalla de 'Signup' intermedio.
        """
        user = super().populate_user(request, sociallogin, data)
        
        # Si no tiene username, generamos uno basado en email
        if not user.username:
            import uuid
            email_part = user.email.split('@')[0]
            # Limpiamos caracteres no alfanumericos
            cleaned_name = "".join(c for c in email_part if c.isalnum())
            # Añadimos sufijo aleatorio corto para evitar colisiones
            user.username = f"{cleaned_name[:20]}_{str(uuid.uuid4())[:8]}"
            
        return user

    def pre_social_login(self, request, sociallogin):
        # Lógica de JIT Provisioning
        user = sociallogin.user
        if not user.email:
            return

        # NEW LOGIC: Conectar automáticamente si el email ya existe
        if not sociallogin.is_existing:
            User = get_user_model()
            try:
                # Buscamos usuario existente por email
                existing_user = User.objects.get(email=user.email)
                # Conectamos la cuenta social al usuario existente
                sociallogin.connect(request, existing_user)
                logger.info(f"Connected existing user {existing_user} to social account via email")
            except User.DoesNotExist:
                # Si no existe, dejamos que siga el flujo de creación (populate_user)
                pass

        email_domain = user.email.split('@')[1] if '@' in user.email else ''

        # LOGIC: Auto-Tenant para AB11
        if email_domain == 'ab11.com.co':
            self._provision_ab11_tenant(user)

    def _provision_ab11_tenant(self, user):
        """
        Crea/Verifica el tenant AB11 y el empleado asociado al usuario.
        """
        try:
            with transaction.atomic():
                # 1. Tenant
                client, created = Client.objects.get_or_create(
                    nit='900000000', # NIT Ficticio/Demo
                    defaults={
                        'name': 'Automatizados AB11 Ltda',
                        'legal_name': 'Automatizados AB11 Limitada',
                        'email': 'admin@ab11.com.co',
                        'phone': '3000000000',
                        'address': 'Calle 123 # 45-67',
                        'tax_regime': 'COMUN'
                    }
                )
                if created:
                    logger.info(f"Tenant AB11 creado: {client}")

                # 2. ThirdParty (El usuario como persona)
                # Buscamos por email y cliente
                third_party, tp_created = ThirdParty.objects.get_or_create(
                    client=client,
                    email=user.email,
                    defaults={
                        'party_type': 'EMPLEADO',
                        'person_type': 2, # Natural
                        'first_name': user.first_name or 'Usuario',
                        'surname': user.last_name or 'AB11',
                        'identification_type': '13', # Cedula
                        'identification_number': user.username, # Fallback ID
                        'address': 'Direccion Registrada',
                        'phone': '0000000',
                        'postal_code': '760001',
                        'city_code': '76001',
                        'department_code': '76',
                    }
                )
                
                # 3. Employee (El perfil de nómina)
                if not hasattr(third_party, 'employee_profile'):
                    # Crear Cost Center dummy si no existe
                    cc, _ = CostCenter.objects.get_or_create(
                        client=client, 
                        code='001', 
                        defaults={'name': 'Operaciones'}
                    )
                    
                    Employee.objects.create(
                        third_party=third_party,
                        code=user.username,
                        contract_type='INDEFINIDO',
                        start_date='2024-01-01',
                        base_salary=1300000,
                        health_entity='EPS SURA',
                        pension_entity='PROTECCION',
                        severance_entity='PROTECCION',
                        arl_entity='SURA',
                        position='Analista',
                        cost_center=cc
                    )
                    logger.info(f"Perfil de Empleado creado para {user.email}")
                    
        except Exception as e:
            logger.error(f"Error en provisionamiento AB11: {str(e)}")
            # No bloqueamos el login, pero logueamos el error
