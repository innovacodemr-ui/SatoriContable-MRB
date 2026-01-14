from django.conf import settings
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.http import JsonResponse
from rest_framework_simplejwt.tokens import RefreshToken
from apps.accounting.models import ThirdParty

@method_decorator(login_required, name='dispatch')
class SocialAuthCallbackView(View):
    """
    Vista de retorno post-login social.
    Genera JWT y redirecciona al Frontend con tokens y Contexto (ClientId).
    """
    def get(self, request):
        user = request.user
        
        # 1. Generar JWT
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        
        # 2. Resolver Client (Tenant)
        client_id = ''
        try:
            tp = ThirdParty.objects.filter(email=user.email).first()
            if tp and tp.client:
                client_id = tp.client.id
        except Exception:
            pass
            
        # 3. Construir URL de retorno (Frontend)
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
        redirect_url = f"{frontend_url}/auth/callback?access={access_token}&refresh={refresh_token}&clientId={client_id}"
        
        return redirect(redirect_url)

class DashboardStatsView(View):
    """
    Vista placeholder para estadisticas del dashboard.
    Restaurada para evitar ImportError.
    """
    def get(self, request):
        return JsonResponse({
            "users": 0,
            "revenue": 0,
            "active_sessions": 0,
            "status": "restored"
        })
