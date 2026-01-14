"""
URL configuration for Satori Accounting System.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

def api_root(request):
    return JsonResponse({
        "system": "Satori Accounting API",
        "version": "1.0.0",
        "status": "online",
        "documentation": "/api/docs/"
    })

# from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    # Root API view
    path('', api_root, name='api-root'),

    # Admin
    path('admin/', admin.site.urls),

    # Init Allauth (SSO)
    path('accounts/', include('allauth.urls')),
    
    # API Documentation
    # path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    # API Endpoints
    path('api/auth/', include('apps.core.urls')),
    path('api/tenants/', include('apps.tenants.urls')),
    path('api/accounting/', include('apps.accounting.urls')),
    path('api/invoicing/', include('apps.invoicing.urls')),
    path('api/taxes/', include('apps.taxes.urls')),
    path('api/dian/', include('apps.dian.urls')),
    path('api/payroll/', include('apps.payroll.urls')),
    path('api/reports/', include('apps.reports.urls')),
    path('api/sync/', include('apps.sync.urls')),
    path('api/radian/', include('apps.electronic_events.urls')), # RADIAN (Recepción)
    path('api/support-docs/', include('apps.support_docs.urls')), # Documento Soporte
    path('api/treasury/', include('apps.treasury.urls')), # Tesorería (Pagos)
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
