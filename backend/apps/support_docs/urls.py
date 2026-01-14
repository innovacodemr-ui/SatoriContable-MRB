from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import SupportDocumentViewSet

router = DefaultRouter()
router.register(r'documents', SupportDocumentViewSet, basename='support-docs')

urlpatterns = [
    # Puedes agregar rutas adicionales aquí si es necesario
] + router.urls
