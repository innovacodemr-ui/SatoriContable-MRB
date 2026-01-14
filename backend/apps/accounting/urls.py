from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'accounts', views.AccountViewSet, basename='account')
router.register(r'cost-centers', views.CostCenterViewSet, basename='cost-center')
router.register(r'third-parties', views.ThirdPartyViewSet, basename='third-party')
router.register(r'journal-entries', views.JournalEntryViewSet, basename='journal-entry')
# Rutas para Motor Contable
router.register(r'accounting-document-types', views.AccountingDocumentTypeViewSet, basename='accounting-document-type')
router.register(r'accounting-templates', views.AccountingTemplateViewSet, basename='accounting-template')
# Rutas para DIAN (dropdowns)
router.register(r'dian-formats', views.DianFormatViewSet, basename='dian-format')
router.register(r'dian-concepts', views.DianConceptViewSet, basename='dian-concept')

urlpatterns = [
    path('', include(router.urls)),
    path('balance-sheet/', views.balance_sheet, name='balance-sheet'),
    path('trial-balance/', views.trial_balance, name='trial-balance'),
    path('income-statement/', views.income_statement, name='income-statement'),
]
