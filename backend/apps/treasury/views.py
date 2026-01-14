from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import BankAccount, PaymentOut
from .serializers import BankAccountSerializer, PaymentOutSerializer
from .services.treasury_service import TreasuryService

class BankAccountViewSet(viewsets.ModelViewSet):
    serializer_class = BankAccountSerializer

    def get_queryset(self):
        return BankAccount.objects.all()

class PaymentOutViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentOutSerializer

    def get_queryset(self):
        return PaymentOut.objects.all().order_by('-created_at')

    @action(detail=True, methods=['post'])
    def post_payment(self, request, pk=None):
        """
        Endpoint to post (contabilizar) the payment.
        Validates structure and calls TreasuryService.
        """
        payment = self.get_object()
        try:
            TreasuryService.post_payment(payment.pk)
            # Re-fetch to get updated status
            payment.refresh_from_db()
            serializer = self.get_serializer(payment)
            return Response(serializer.data)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': f"Error interno: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
