from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UploadInvoiceView, ListInvoicesView, SendEventView, SyncEmailView, ReceivedInvoiceViewSet

router = DefaultRouter()
router.register(r'invoices', ReceivedInvoiceViewSet, basename='received-invoice')

urlpatterns = [
    path('receive/upload/', UploadInvoiceView.as_view(), name='radian_upload'),
    path('receive/list/', ListInvoicesView.as_view(), name='radian_list'),
    path('receive/sync-email/', SyncEmailView.as_view(), name='radian_sync_email'),
    path('send-event/<int:invoice_id>/', SendEventView.as_view(), name='radian_send_event'),
    path('', include(router.urls)), # Exposes /electronic-events/invoices/
]
