from rest_framework import serializers
from apps.dian.models import ElectronicDocument, ElectronicDocumentLine, DIANResolution


class ElectronicDocumentLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = ElectronicDocumentLine
        fields = '__all__'


class ElectronicDocumentSerializer(serializers.ModelSerializer):
    lines = ElectronicDocumentLineSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    
    class Meta:
        model = ElectronicDocument
        fields = '__all__'


class DIANResolutionSerializer(serializers.ModelSerializer):
    available_numbers = serializers.SerializerMethodField()
    
    class Meta:
        model = DIANResolution
        fields = '__all__'
    
    def get_available_numbers(self, obj):
        return obj.get_available_numbers()
