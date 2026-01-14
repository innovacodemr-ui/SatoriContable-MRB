from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from apps.accounting.models import ThirdParty
from apps.tenants.models import Client

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        # Logica para determinar client_id
        user = self.user
        client_id = None
        
        # 1. Buscar por email en ThirdParty (empleados, contadores, etc vinculados)
        #    Esta es la logica actual usada en SocialAuthCallbackView
        try:
            tp = ThirdParty.objects.filter(email=user.email).first()
            if tp and tp.client:
                client_id = tp.client.id
        except Exception:
            pass
            
        # 2. Fallback para superusuarios: Si no tiene ThirdParty, asignamos el primer cliente
        #    para evitar que se queden sin acceso al dashboard.
        if not client_id and user.is_superuser:
            first_client = Client.objects.first()
            if first_client:
                client_id = first_client.id
        
        # CRÍTICO: Incluir client_id en el token para validación de seguridad
        if client_id:
            data['client_id'] = client_id
            # También lo agregamos al refresh token
            refresh = self.get_token(self.user)
            refresh['client_id'] = client_id
            
        return data
