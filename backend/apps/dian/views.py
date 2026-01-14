from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from apps.dian.models import ElectronicDocument, DIANResolution
from apps.dian.serializers import ElectronicDocumentSerializer, DIANResolutionSerializer


class ElectronicDocumentViewSet(viewsets.ModelViewSet):
    serializer_class = ElectronicDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['document_type', 'status', 'issue_date']
    search_fields = ['full_number', 'customer__business_name']

    def get_queryset(self):
        return ElectronicDocument.objects.all()


class DIANResolutionViewSet(viewsets.ModelViewSet):
    serializer_class = DIANResolutionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['is_active', 'is_test']

    def get_queryset(self):
        return DIANResolution.objects.all()


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def send_to_dian(request, pk):
    """Enviar documento a la DIAN"""
    # TODO: Implementar lógica de envío a DIAN
    return Response({'message': 'Documento enviado a DIAN'})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def validate_document(request, pk):
    """Validar documento electrónico"""
    # TODO: Implementar lógica de validación
    return Response({'message': 'Documento validado'})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def generate_pdf(request, pk):
    """Generar PDF del documento"""
    # TODO: Implementar generación de PDF
    return Response({'message': 'PDF generado'})
