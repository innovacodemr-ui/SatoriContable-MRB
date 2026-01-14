from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Client
from .serializers import ClientSerializer, ClientCreateSerializer
from .utils import get_current_client_id


class ClientViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de clientes/empresas (multi-tenant).
    """
    queryset = Client.objects.all()
    # TODO: Filtrar queryset por usuario/permissions
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ClientCreateSerializer
        return ClientSerializer
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """
        Retorna la empresa actual basada en el contexto (X-Client-Id).
        """
        tenant_id = get_current_client_id()
        
        if not tenant_id:
            return Response(
                {"error": "No se ha identificado la empresa. Header 'X-Client-Id' faltante o inválido."}, 
                status=400
            )

        try:
            client = Client.objects.get(pk=tenant_id)
        except Client.DoesNotExist:
            return Response({"error": "Empresa no encontrada"}, status=404)

        serializer = self.get_serializer(client)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def sync(self, request, pk=None):
        """
        Forzar sincronización de datos para un cliente específico.
        """
        client = self.get_object()
        # TODO: Implementar lógica de sincronización
        return Response({
            'status': 'success',
            'message': f'Sincronización iniciada para {client.name}'
        })
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """
        Obtener estado actual del cliente.
        """
        client = self.get_object()
        return Response({
            'name': client.name,
            'nit': client.nit,
            'is_active': client.is_active,
            'plan': client.plan,
            'sync_enabled': client.sync_enabled,
            'last_sync': client.last_sync,
        })
