from rest_framework import viewsets, filters 
from rest_framework.permissions import IsAuthenticated
from .models import DianResolution, Item, Invoice
from .serializers import DianResolutionSerializer, ItemSerializer, InvoiceSerializer

class DianResolutionViewSet(viewsets.ModelViewSet):
    serializer_class = DianResolutionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['document_type', 'is_active']
    pagination_class = None # Enable loading all in select

    def get_queryset(self):
        return DianResolution.objects.all()

class ItemViewSet(viewsets.ModelViewSet):
    serializer_class = ItemSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['code', 'description']

    def get_queryset(self):
        return Item.objects.all()

class InvoiceViewSet(viewsets.ModelViewSet):
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status', 'customer']

    def get_queryset(self):
        return Invoice.objects.all().order_by('-id')

