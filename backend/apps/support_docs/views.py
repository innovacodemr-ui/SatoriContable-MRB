from rest_framework import viewsets, permissions
from .models import SupportDocument
from .serializers import SupportDocumentSerializer

class SupportDocumentViewSet(viewsets.ModelViewSet):
    serializer_class = SupportDocumentSerializer
    permission_classes = [permissions.AllowAny] # Ajustar a IsAuthenticated en producción real

    def get_queryset(self):
        return SupportDocument.objects.all().order_by('-id')

    def perform_create(self, serializer):
        # Asignar cliente por defecto o del usuario logueado
        # serializer.save(client=self.request.user.client)
        pass # ToDo: Implementar lógica de asignación de cliente y consecutivo

