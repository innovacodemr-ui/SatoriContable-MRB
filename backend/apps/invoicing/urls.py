from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DianResolutionViewSet, ItemViewSet, InvoiceViewSet

router = DefaultRouter()
router.register(r'resolutions', DianResolutionViewSet, basename='invoicing-resolution')
router.register(r'items', ItemViewSet, basename='invoicing-item')
router.register(r'invoices', InvoiceViewSet, basename='invoicing-invoice')

urlpatterns = [
    path('', include(router.urls)),
]
