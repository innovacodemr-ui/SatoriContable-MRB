from django.core.management.base import BaseCommand
from apps.payroll.models import PayrollConcept

class Command(BaseCommand):
    help = 'Limpia y repuebla la tabla maestra de Conceptos de Nómina con normativa legal COL y códigos DIAN'

    def handle(self, *args, **kwargs):
        self.stdout.write("Iniciando carga de Conceptos de Nómina (Tabla Maestra)...")
        
        # Eliminar anteriores para evitar duplicados o sucios
        PayrollConcept.objects.all().delete()
        
        concepts = [
            # --- DEVENGADOS SALARIALES ---
            {
                "code": "BASICO", "name": "Sueldo Básico", "type": "EARNING", "dian_code": "BASICO", 
                "is_salary": True, "percentage": 0
            },
            {
                "code": "HED", "name": "Hora Extra Diurna", "type": "EARNING", "dian_code": "HED", 
                "is_salary": True, "percentage": 25.00
            },
            {
                "code": "HEN", "name": "Hora Extra Nocturna", "type": "EARNING", "dian_code": "HEN", 
                "is_salary": True, "percentage": 75.00
            },
            {
                "code": "HRN", "name": "Recargo Nocturno", "type": "EARNING", "dian_code": "HRN", 
                "is_salary": True, "percentage": 35.00
            },
            {
                "code": "HEDDF", "name": "Hora Extra Diurna Dom/Fest", "type": "EARNING", "dian_code": "HEDDF", 
                "is_salary": True, "percentage": 100.00
            },
            {
                "code": "HENDF", "name": "Hora Extra Nocturna Dom/Fest", "type": "EARNING", "dian_code": "HENDF", 
                "is_salary": True, "percentage": 150.00
            },
            {
                "code": "HRDDF", "name": "Recargo Diurno Dom/Fest", "type": "EARNING", "dian_code": "HRDDF", 
                "is_salary": True, "percentage": 75.00
            },
            {
                "code": "HRNDF", "name": "Recargo Nocturno Dom/Fest", "type": "EARNING", "dian_code": "HRNDF", 
                "is_salary": True, "percentage": 110.00 # 75% Festivo + 35% Nocturno
            },
            {
                "code": "COMISION", "name": "Comisiones", "type": "EARNING", "dian_code": "COMISION", 
                "is_salary": True, "percentage": 0
            },
            {
                "code": "BONIF_SALARIAL", "name": "Bonificación Salarial", "type": "EARNING", "dian_code": "BONIFICACION_S", 
                "is_salary": True, "percentage": 0
            },
            {
                "code": "VACACIONES_DISFRUTE", "name": "Vacaciones Disfrutadas", "type": "EARNING", "dian_code": "VACACIONES_COMUNES", 
                "is_salary": True, "percentage": 0
            },
            {
                "code": "VACACIONES_DINERO", "name": "Vacaciones Compensadas (Dinero)", "type": "EARNING", "dian_code": "VACACIONES_COMPENSADAS", 
                "is_salary": True, "percentage": 0
            },
            {
                "code": "INCAPACIDAD", "name": "Incapacidad General", "type": "EARNING", "dian_code": "INCAPACIDAD", 
                "is_salary": True, "percentage": 66.67
            },
             {
                "code": "LICENCIA_MAT", "name": "Licencia Maternidad/Paternidad", "type": "EARNING", "dian_code": "LICENCIA_MP", 
                "is_salary": True, "percentage": 100.00
            },
            {
                "code": "LICENCIA_REM", "name": "Licencia Remunerada", "type": "EARNING", "dian_code": "LICENCIA_R", 
                "is_salary": True, "percentage": 100.00
            },

            # --- DEVENGADOS NO SALARIALES ---
            {
                "code": "TRANSPORTE", "name": "Auxilio de Transporte", "type": "EARNING", "dian_code": "AUX_TRANSPORTE", 
                "is_salary": False, "percentage": 0
            },
            {
                "code": "CONECTIVIDAD", "name": "Auxilio de Conectividad (Digital)", "type": "EARNING", "dian_code": "AUX_CONECTIVIDAD", 
                "is_salary": False, "percentage": 0 
                # Nota: Legalmente sustituye al aux transporte, no suman ambos.
            },
            {
                "code": "BONIF_NO_SALARIAL", "name": "Bonificación No Salarial", "type": "EARNING", "dian_code": "BONIFICACION_NS", 
                "is_salary": False, "percentage": 0
            },
             {
                "code": "VIATICOS_MANU_ALOJ", "name": "Viáticos Manut. y Alojamiento (No Salarial)", "type": "EARNING", "dian_code": "VIATICO_MANU_ALOJ_NS", 
                "is_salary": False, "percentage": 0
            },

            # --- DEDUCCIONES ---
            {
                "code": "SALUD", "name": "Aporte Salud (Empleado)", "type": "DEDUCTION", "dian_code": "SALUD", 
                "is_salary": False, "percentage": 4.00
            },
            {
                "code": "PENSION", "name": "Aporte Pensión (Empleado)", "type": "DEDUCTION", "dian_code": "PENSION", 
                "is_salary": False, "percentage": 4.00
            },
            {
                "code": "FSP_SOL", "name": "Fondo Solidaridad Pensional", "type": "DEDUCTION", "dian_code": "FSP", 
                "is_salary": False, "percentage": 1.00 # Base minima
            },
            {
                "code": "FSP_SUB", "name": "Fondo Subsistencia", "type": "DEDUCTION", "dian_code": "FSP_SUBSISTENCIA", 
                "is_salary": False, "percentage": 0 # Variable segun rango
            },
            {
                "code": "RETENCION", "name": "Retención en la Fuente", "type": "DEDUCTION", "dian_code": "RETENCION_FUENTE", 
                "is_salary": False, "percentage": 0
            },
            {
                "code": "LIBRANZA", "name": "Libranza / Prestamo", "type": "DEDUCTION", "dian_code": "LIBRANZA", 
                "is_salary": False, "percentage": 0
            },
            {
                "code": "SINDICATO", "name": "Cuota Sindical", "type": "DEDUCTION", "dian_code": "SINDICATO", 
                "is_salary": False, "percentage": 0
            },
            {
                "code": "SANCION", "name": "Sanción Disciplinaria", "type": "DEDUCTION", "dian_code": "SANCION", 
                "is_salary": False, "percentage": 0
            },
        ]

        count = 0
        for data in concepts:
            PayrollConcept.objects.create(
                code=data['code'],
                name=data['name'],
                concept_type=data['type'],
                dian_code=data['dian_code'],
                is_salary=data['is_salary'],
                percentage=data['percentage']
            )
            count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Base de datos actualizada con {count} Conceptos de Nómina Estándar DIAN.'))
