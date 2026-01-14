from rest_framework import serializers
from .models import ReceivedInvoice, InvoiceEvent

class InvoiceEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceEvent
        fields = '__all__'

class ReceivedInvoiceSerializer(serializers.ModelSerializer):
    events = InvoiceEventSerializer(many=True, read_only=True)
    
    class Meta:
        model = ReceivedInvoice
        fields = '__all__'
