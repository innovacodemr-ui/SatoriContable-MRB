from rest_framework import serializers
from .models import Client
from apps.common.utils import SecurityService

class ClientSerializer(serializers.ModelSerializer):
    certificate_password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    has_certificate = serializers.SerializerMethodField()
    
    class Meta:
        model = Client
        fields = [
            'id', 'name', 'nit', 'legal_name', 'business_name',
            'tax_regime', 'fiscal_responsibilities', 'address', 'city', 'department',
            'country', 'postal_code', 'phone', 'email', 'website',
            'dian_software_id', 'dian_test_set_id', 'plan', 'is_active',
            'sync_enabled', 'last_sync', 'created_on', 'modified_on',
            'logo', 'dian_certificate', 'certificate_password', 'certificate_password_encrypted',
            'has_certificate'
        ]
        read_only_fields = ['created_on', 'modified_on', 'last_sync', 'certificate_password_encrypted', 'has_certificate']
        extra_kwargs = {
            'dian_certificate': {'write_only': True} # Para no exponer la URL directa si no se desea
        }

    def get_has_certificate(self, obj):
        return bool(obj.dian_certificate)

    def update(self, instance, validated_data):
        # Interceptar contraseña plana y cifrarla
        password = validated_data.pop('certificate_password', None)
        if password:
            instance.certificate_password_encrypted = SecurityService.encrypt_password(password)
        
        return super().update(instance, validated_data)

class ClientCreateSerializer(serializers.ModelSerializer):
    domain = serializers.CharField(write_only=True, help_text="Dominio principal para el cliente")
    
    class Meta:
        model = Client
        fields = [
            'schema_name', 'name', 'nit', 'legal_name', 'business_name',
            'tax_regime', 'fiscal_responsibilities', 'address', 'city', 'department',
            'country', 'postal_code', 'phone', 'email', 'website', 'plan', 'domain'
        ]
    
    def create(self, validated_data):
        domain_name = validated_data.pop('domain')
        client = Client.objects.create(**validated_data)
        
        # Crear dominio principal
        Domain.objects.create(
            domain=domain_name,
            tenant=client,
            is_primary=True
        )
        
        return client
