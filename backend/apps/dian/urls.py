from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'electronic-documents', views.ElectronicDocumentViewSet, basename='electronic-document')
router.register(r'resolutions', views.DIANResolutionViewSet, basename='dian-resolution')

urlpatterns = [
    path('', include(router.urls)),
    path('send/<int:pk>/', views.send_to_dian, name='send-to-dian'),
    path('validate/<int:pk>/', views.validate_document, name='validate-document'),
    path('generate-pdf/<int:pk>/', views.generate_pdf, name='generate-pdf'),
]
