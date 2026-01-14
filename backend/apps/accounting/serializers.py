from rest_framework import serializers
from apps.accounting.models import (
    Account, AccountClass, AccountGroup, AccountDianConfiguration,
    CostCenter, ThirdParty, JournalEntry, JournalEntryLine,
    DianFormat, DianConcept, AccountingTemplate, AccountingTemplateLine, AccountingDocumentType
)


class DianFormatSerializer(serializers.ModelSerializer):
    class Meta:
        model = DianFormat
        fields = '__all__'


class DianConceptSerializer(serializers.ModelSerializer):
    dian_format_id = serializers.PrimaryKeyRelatedField(
        source='format', 
        queryset=DianFormat.objects.all(),
        # write_only=False so it's included in serialization
    )

    class Meta:
        model = DianConcept
        fields = ['id', 'dian_format_id', 'code', 'name', 'description']



class AccountDianConfigurationSerializer(serializers.ModelSerializer):
    format_code = serializers.CharField(source='dian_format.code', read_only=True)
    format_name = serializers.CharField(source='dian_format.name', read_only=True)
    concept_code = serializers.CharField(source='dian_concept.code', read_only=True)
    concept_name = serializers.CharField(source='dian_concept.name', read_only=True)
    
    class Meta:
        model = AccountDianConfiguration
        fields = ['id', 'dian_format', 'dian_concept', 'format_code', 'format_name', 'concept_code', 'concept_name']


class AccountClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountClass
        fields = '__all__'


class AccountGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountGroup
        fields = '__all__'


class AccountSerializer(serializers.ModelSerializer):
    balance = serializers.SerializerMethodField()
    dian_configurations = AccountDianConfigurationSerializer(many=True, required=False)
    
    class Meta:
        model = Account
        fields = '__all__'
    
    def get_balance(self, obj):
        return obj.get_balance()
    
    def create(self, validated_data):
        dian_configs = validated_data.pop('dian_configurations', [])
        account = Account.objects.create(**validated_data)
        
        for config in dian_configs:
            AccountDianConfiguration.objects.create(account=account, **config)
            
        return account

    def update(self, instance, validated_data):
        dian_configs = validated_data.pop('dian_configurations', None)
        
        # Actualizar campos normales
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Actualizar configuraciones DIAN si se enviaron
        if dian_configs is not None:
            # Estrategia simple: borrar y recrear
            instance.dian_configurations.all().delete()
            for config in dian_configs:
                AccountDianConfiguration.objects.create(account=instance, **config)
                
        return instance


class CostCenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CostCenter
        fields = '__all__'


class ThirdPartySerializer(serializers.ModelSerializer):
    check_digit = serializers.CharField(read_only=True)  # Auto-calculado
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ThirdParty
        fields = '__all__'
        read_only_fields = ['check_digit', 'created_at', 'updated_at']
    
    def get_full_name(self, obj):
        """Retorna el nombre completo según el tipo de persona"""
        return obj.get_full_name()
    
    def validate(self, data):
        """Validaciones DIAN"""
        # Validar que Persona Jurídica tenga razón social
        if data.get('person_type') == 1 and not data.get('business_name'):
            raise serializers.ValidationError({
                'business_name': 'La razón social es obligatoria para Persona Jurídica'
            })
        
        # Validar que Persona Natural tenga nombre y apellido
        if data.get('person_type') == 2:
            if not data.get('first_name'):
                raise serializers.ValidationError({
                    'first_name': 'El primer nombre es obligatorio para Persona Natural'
                })
            if not data.get('surname'):
                raise serializers.ValidationError({
                    'surname': 'El primer apellido es obligatorio para Persona Natural'
                })
        
        return data


class JournalEntryLineSerializer(serializers.ModelSerializer):
    account_code = serializers.CharField(source='account.code', read_only=True)
    account_name = serializers.CharField(source='account.name', read_only=True)
    
    class Meta:
        model = JournalEntryLine
        fields = '__all__'


class JournalEntrySerializer(serializers.ModelSerializer):
    lines = JournalEntryLineSerializer(many=True, read_only=True)
    total_debit = serializers.SerializerMethodField()
    total_credit = serializers.SerializerMethodField()
    is_balanced = serializers.SerializerMethodField()
    
    # Campo calculado para información de documento origen
    source_document_info = serializers.SerializerMethodField()
    
    class Meta:
        model = JournalEntry
        fields = '__all__'
    
    def get_total_debit(self, obj):
        return obj.get_total_debit()
    
    def get_total_credit(self, obj):
        return obj.get_total_credit()
    
    def get_is_balanced(self, obj):
        return obj.is_balanced()

    def get_source_document_info(self, obj):
        """Retorna info básica del documento origen si existe"""
        if obj.content_object:
            return {
                "type": obj.content_type.model, # ej: receivedinvoice
                "app_label": obj.content_type.app_label, # ej: electronic_events
                "id": obj.object_id,
                "str_repr": str(obj.content_object)
            }
        return None

# ==========================================
#  ORDEN #3 - SERIALIZADORES DEL MOTOR CONTABLE
# ==========================================

class AccountingDocumentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccountingDocumentType
        fields = '__all__'


class AccountingTemplateLineSerializer(serializers.ModelSerializer):
    account_code = serializers.CharField(source='account.code', read_only=True)
    account_name = serializers.CharField(source='account.name', read_only=True)
    
    class Meta:
        model = AccountingTemplateLine
        fields = ['id', 'account', 'account_code', 'account_name', 'nature', 'calculation_method', 'value', 'description_template']


class AccountingTemplateSerializer(serializers.ModelSerializer):
    lines = AccountingTemplateLineSerializer(many=True)
    document_type_name = serializers.CharField(source='document_type.name', read_only=True)

    class Meta:
        model = AccountingTemplate
        fields = ['id', 'name', 'document_type', 'document_type_name', 'active', 'lines', 'created_at', 'updated_at']

    def create(self, validated_data):
        lines_data = validated_data.pop('lines')
        template = AccountingTemplate.objects.create(**validated_data)
        
        for line_data in lines_data:
            AccountingTemplateLine.objects.create(template=template, **line_data)
        
        return template

    def update(self, instance, validated_data):
        lines_data = validated_data.pop('lines', None)
        
        # Actualizar campos simples
        instance.name = validated_data.get('name', instance.name)
        instance.document_type = validated_data.get('document_type', instance.document_type)
        instance.active = validated_data.get('active', instance.active)
        instance.save()
        
        # Actualizar líneas si vienen
        if lines_data is not None:
            instance.lines.all().delete() # Estrategia simple: Borrar y recrear
            for line_data in lines_data:
                AccountingTemplateLine.objects.create(template=instance, **line_data)
        
        return instance

