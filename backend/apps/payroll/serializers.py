from rest_framework import serializers
from .models import LegalParameter, NoveltyType, EmployeeNovelty, Employee, PayrollPeriod, PayrollDocument, PayrollDetail
import datetime
from django.db.models import Q

class LegalParameterSerializer(serializers.ModelSerializer):
    key_display = serializers.CharField(source='get_key_display', read_only=True)
    class Meta:
        model = LegalParameter
        fields = '__all__'

class NoveltyTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = NoveltyType
        fields = '__all__'

class EmployeeNoveltySerializer(serializers.ModelSerializer):
    # Output fields
    novelty_name = serializers.CharField(source='novelty_type.name', read_only=True)
    employee_name = serializers.CharField(source='employee.third_party.get_full_name', read_only=True)
    document_url = serializers.FileField(source='attachment', read_only=True)
    
    # Input fields
    novelty_code = serializers.CharField(write_only=True)
    
    class Meta:
        model = EmployeeNovelty
        fields = [
            'id', 'employee', 'employee_name', 
            'novelty_type', 'novelty_code', 'novelty_name',
            'start_date', 'end_date', 'days', 'total_value',
            'attachment', 'document_url'
        ]
        read_only_fields = ['novelty_type', 'total_value', 'end_date']

    def validate(self, data):
        """
        Validación cruzada: solapamiento, cálculo de fechas y búsqueda de novedad por código.
        """
        # 1. Resolver Novelty Code -> Type
        novelty_code = data.get('novelty_code')
        try:
            novelty = NoveltyType.objects.get(code=novelty_code)
            data['novelty_type'] = novelty
        except NoveltyType.DoesNotExist:
            raise serializers.ValidationError({"novelty_code": f"El código de novedad '{novelty_code}' no existe."})

        # 2. Calcular End Date si no viene, o validar consistencia
        start_date = data.get('start_date')
        days = data.get('days')

        if not days or days <= 0:
             raise serializers.ValidationError({"days": "La cantidad de días debe ser mayor a 0."})

        # Calculamos end_date basado en start_date + days - 1
        # Ej: 1 día empezando el 20, termina el 20. (20 + 1 - 1 = 20)
        calculated_end_date = start_date + datetime.timedelta(days=days-1)
        data['end_date'] = calculated_end_date

        # 3. Validar Solapamiento (Overlap)
        employee = data.get('employee')
        
        # Buscar novedades existentes que se solapen
        # (StartA <= EndB) and (EndA >= StartB)
        overlapping = EmployeeNovelty.objects.filter(
            employee=employee
        ).filter(
            Q(start_date__lte=calculated_end_date) & Q(end_date__gte=start_date)
        )
        
        # Si es update, excluir la propia instancia
        if self.instance:
            overlapping = overlapping.exclude(pk=self.instance.pk)
            
        if overlapping.exists():
            conflict = overlapping.first()
            raise serializers.ValidationError(
                f"El empleado ya tiene una novedad registrada en estas fechas: {conflict.novelty_type.name} ({conflict.start_date} a {conflict.end_date})"
            )
        
        return data

    def create(self, validated_data):
        # Extraer novelty_code porque no es campo del modelo
        validated_data.pop('novelty_code', None)
        return super().create(validated_data)

class EmployeeSerializer(serializers.ModelSerializer):
    third_party_name = serializers.CharField(source='third_party.get_full_name', read_only=True)
    third_party_nit = serializers.CharField(source='third_party.identification_number', read_only=True)
    
    class Meta:
        model = Employee
        fields = '__all__'

class PayrollDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollDetail
        fields = '__all__'

class PayrollDocumentSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.third_party.get_full_name', read_only=True)
    details = PayrollDetailSerializer(many=True, read_only=True)
    
    class Meta:
        model = PayrollDocument
        fields = '__all__'

class PayrollPeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollPeriod
        fields = '__all__'
