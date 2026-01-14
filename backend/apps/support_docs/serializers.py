from rest_framework import serializers
from .models import SupportDocument, DianResolution

class DianResolutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DianResolution
        fields = '__all__'

class SupportDocumentSerializer(serializers.ModelSerializer):
    status_label = serializers.CharField(source='get_dian_status_display', read_only=True)
    
    class Meta:
        model = SupportDocument
        fields = '__all__'
        read_only_fields = ('consecutive', 'cuds', 'xml_file', 'pdf_file', 'client')
