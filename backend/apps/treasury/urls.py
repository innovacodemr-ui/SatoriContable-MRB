from rest_framework.routers import DefaultRouter
from .views import BankAccountViewSet, PaymentOutViewSet

router = DefaultRouter()
router.register(r'bank-accounts', BankAccountViewSet, basename='bank-account')
router.register(r'payments', PaymentOutViewSet, basename='payment-out')

urlpatterns = router.urls
