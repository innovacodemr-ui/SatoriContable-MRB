from rest_framework import serializers
from .models import DianResolution, Item, Invoice, InvoiceLine

class DianResolutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DianResolution
        fields = '__all__'

class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = '__all__'

class InvoiceLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceLine
        fields = ['id', 'item', 'description', 'quantity', 'unit_price', 'tax_rate', 'subtotal', 'tax_amount', 'total']
        read_only_fields = ['subtotal', 'tax_amount', 'total']

class InvoiceSerializer(serializers.ModelSerializer):
    lines = InvoiceLineSerializer(many=True)
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    
    class Meta:
        model = Invoice
        fields = ['id', 'resolution', 'prefix', 'number', 'customer', 'customer_name', 
                  'issue_date', 'payment_due_date', 'payment_term', 
                  'subtotal', 'tax_total', 'total', 'status', 'notes', 'lines']
        read_only_fields = ['prefix', 'number', 'subtotal', 'tax_total', 'total', 'status']

    def create(self, validated_data):
        lines_data = validated_data.pop('lines')
        resolution = validated_data['resolution']
        
        # Auto-assign number from resolution
        # WARNING: Needs transaction lock in production for concurrency
        validated_data['prefix'] = resolution.prefix
        validated_data['number'] = resolution.current_number
        
        invoice = Invoice.objects.create(**validated_data)
        
        # Increment resolution
        resolution.current_number += 1
        resolution.save()
        
        # Create lines and sum totals
        subtotal = 0
        tax_total = 0
        
        for line_data in lines_data:
            line = InvoiceLine.objects.create(invoice=invoice, **line_data)
            subtotal += line.subtotal
            tax_total += line.tax_amount
            
        invoice.subtotal = subtotal
        invoice.tax_total = tax_total
        invoice.total = subtotal + tax_total
        invoice.save()
        
        return invoice

