from apps.tenants.utils import set_current_client_id
from django.http import JsonResponse
import jwt
from django.conf import settings

class TenantMiddleware:
    """
    Middleware de seguridad CRÍTICO.
    Extrae el X-Client-Id de la cabecera e inyecta el contexto del tenant
    en el almacenamiento local del hilo (Thread Local Storage) antes de procesar la vista.
    
    SEGURIDAD: Valida que el X-Client-Id coincida con el client_id del JWT para prevenir IDOR.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. IDENTIFICACIÓN: Obtener el ID del tenant de los headers
        tenant_id = request.headers.get('X-Client-Id')

        # 2. VALIDACIÓN DE SEGURIDAD: Verificar que el tenant_id coincida con el JWT
        # Solo para rutas API autenticadas (excluir admin, static, accounts)
        if tenant_id and request.path.startswith('/api/') and 'Authorization' in request.headers:
            try:
                # Extraer y decodificar el JWT
                auth_header = request.headers.get('Authorization', '')
                if auth_header.startswith('Bearer '):
                    token = auth_header.split(' ')[1]
                    # Decodificar sin verificar (ya lo hace DRF), solo para leer claims
                    decoded = jwt.decode(token, options={"verify_signature": False})
                    jwt_client_id = decoded.get('client_id')
                    
                    # VALIDACIÓN CRÍTICA: El client_id del JWT debe coincidir con X-Client-Id
                    if jwt_client_id and str(jwt_client_id) != str(tenant_id):
                        return JsonResponse({
                            'error': 'Forbidden',
                            'detail': 'El Client-Id del header no coincide con tu organización.'
                        }, status=403)
            except (jwt.DecodeError, jwt.InvalidTokenError, KeyError):
                # Si hay error decodificando, permitir que DRF maneje la autenticación
                pass

        # 3. CONTEXTO: Establecer el tenant en el thread-local
        # Si tenant_id es None, el Manager filtrará devolviendo vacío (Fail-Safe)
        set_current_client_id(tenant_id)

        try:
            # Procesar la petición
            response = self.get_response(request)
        finally:
            # 3. LIMPIEZA: Paso obligatorio de seguridad.
            # Se resetea el contexto al finalizar la petición para evitar
            # que un hilo reutilizado exponga datos de este tenant a la siguiente petición.
            set_current_client_id(None)

        return response
