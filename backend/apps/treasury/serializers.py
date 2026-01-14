from rest_framework import serializers
from .models import BankAccount, PaymentOut, PaymentOutDetail
from apps.electronic_events.models import ReceivedInvoice

class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = '__all__'

class PaymentOutDetailSerializer(serializers.ModelSerializer):
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True)
    
    class Meta:
        model = PaymentOutDetail
        fields = ['id', 'invoice', 'invoice_number', 'amount_paid']

class PaymentOutSerializer(serializers.ModelSerializer):
    details = PaymentOutDetailSerializer(many=True, read_only=False)
    bank_account_name = serializers.CharField(source='bank_account.name', read_only=True)
    
    class Meta:
        model = PaymentOut
        fields = [
            'id', 'consecutive', 'payment_date', 'third_party', 
            'bank_account', 'bank_account_name', 'payment_method', 
            'total_amount', 'notes', 'status', 'details', 'created_at'
        ]
        read_only_fields = ['consecutive', 'status', 'created_at']

    def create(self, validated_data):
        details_data = validated_data.pop('details')
        payment = PaymentOut.objects.create(**validated_data)
        
        for detail_data in details_data:
            PaymentOutDetail.objects.create(payment_out=payment, **detail_data)
            
        return payment

    def update(self, instance, validated_data):
        details_data = validated_data.pop('details', None)
        
        # Update fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update details (replace logic for simplicity in MVP)
        if details_data is not None:
            instance.details.all().delete()
            for detail_data in details_data:
                PaymentOutDetail.objects.create(payment_out=instance, **detail_data)
                
        return instance
