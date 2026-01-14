from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LegalParameterViewSet, NoveltyTypeViewSet, EmployeeNoveltyViewSet,
    EmployeeViewSet, PayrollPeriodViewSet, PayrollDocumentViewSet
)

router = DefaultRouter()
router.register(r'legal-parameters', LegalParameterViewSet, basename='payroll-legal-parameter')
router.register(r'novelty-types', NoveltyTypeViewSet, basename='payroll-novelty-type')
router.register(r'employee-novelties', EmployeeNoveltyViewSet, basename='payroll-employee-novelty')
router.register(r'employees', EmployeeViewSet, basename='payroll-employee')
router.register(r'periods', PayrollPeriodViewSet, basename='payroll-period')
router.register(r'documents', PayrollDocumentViewSet, basename='payroll-document')

urlpatterns = [
    path('', include(router.urls)),
]
