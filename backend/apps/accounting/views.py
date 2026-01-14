from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Sum, Q
from apps.accounting.models import (
    Account, CostCenter, ThirdParty, JournalEntry,
    DianFormat, DianConcept, AccountingTemplate, AccountingDocumentType
)
from apps.accounting.serializers import (
    AccountSerializer, CostCenterSerializer,
    ThirdPartySerializer, JournalEntrySerializer,
    DianFormatSerializer, DianConceptSerializer,
    AccountingTemplateSerializer, AccountingDocumentTypeSerializer
)
from apps.accounting.filters import DianConceptFilter
from django_filters.rest_framework import DjangoFilterBackend


class DianFormatViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar Formatos DIAN"""
    serializer_class = DianFormatSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['code', 'name']

    def get_queryset(self):
        return DianFormat.objects.all()


class DianConceptViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar Conceptos DIAN"""
    serializer_class = DianConceptSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = DianConceptFilter
    search_fields = ['code', 'name']

    def get_queryset(self):
        return DianConcept.objects.all()


class AccountViewSet(viewsets.ModelViewSet):
    serializer_class = AccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['account_type', 'is_active', 'level']
    search_fields = ['code', 'name']
    pagination_class = None  # Deshabilitar paginación para cargar todo el árbol de cuentas

    def get_queryset(self):
        return Account.objects.all()


class CostCenterViewSet(viewsets.ModelViewSet):
    serializer_class = CostCenterSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['code', 'name']

    def get_queryset(self):
        return CostCenter.objects.all()


class ThirdPartyViewSet(viewsets.ModelViewSet):
    serializer_class = ThirdPartySerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['party_type', 'person_type', 'identification_type', 'tax_regime', 'is_active']
    search_fields = ['identification_number', 'first_name', 'surname', 'business_name', 'trade_name', 'email']

    def get_queryset(self):
        return ThirdParty.objects.all()


class JournalEntryViewSet(viewsets.ModelViewSet):
    serializer_class = JournalEntrySerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['status', 'entry_type', 'date']
    search_fields = ['number', 'description']

    def get_queryset(self):
        return JournalEntry.objects.all()


# ==========================================
#  ORDEN #3 - VISTAS DEL MOTOR CONTABLE
# ==========================================

class AccountingDocumentTypeViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar Tipos de Documentos Contables"""
    serializer_class = AccountingDocumentTypeSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['code', 'name']

    def get_queryset(self):
        return AccountingDocumentType.objects.all()


class AccountingTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar Plantillas Contables.
    Permite CRUD completo de Plantillas y sus Líneas anidadas (via serializer).
    """
    serializer_class = AccountingTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['name']
    filterset_fields = ['active', 'document_type']

    def get_queryset(self):
        return AccountingTemplate.objects.all()


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def balance_sheet(request):
    """Balance General"""
    # TODO: Implementar lógica de Balance General
    return Response({'message': 'Balance General'})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def trial_balance(request):
    """Balance de Comprobación"""
    # TODO: Implementar lógica de Balance de Comprobación
    return Response({'message': 'Balance de Comprobación'})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def income_statement(request):
    """Estado de Resultados"""
    # TODO: Implementar lógica de Estado de Resultados
    return Response({'message': 'Estado de Resultados'})
