from django.core.management.base import BaseCommand
from apps.payroll.models import Employee, LegalParameter, NoveltyType
from apps.accounting.models import ThirdParty, CostCenter
from decimal import Decimal
from datetime import date
import random

class Command(BaseCommand):
    help = 'Carga 15 empleados de prueba con datos variados para Test-Drive'

    def handle(self, *args, **options):
        self.stdout.write("Creando empleados de demostración...")

        # 1. Asegurar Centro de Costo por defecto
        cost_center, _ = CostCenter.objects.get_or_create(
            code="ADM",
            defaults={'name': 'Administración General', 'is_active': True}
        )
        
        ops_center, _ = CostCenter.objects.get_or_create(
            code="OPR", 
            defaults={'name': 'Operaciones y Planta', 'is_active': True}
        )

        sale_center, _ = CostCenter.objects.get_or_create(
            code="COM",
            defaults={'name': 'Comercial y Ventas', 'is_active': True}
        )

        # 2. Lista de Empleados Dummy
        employees_data = [
            {
                "id_num": "1010101001", "first_name": "Juan", "surname": "Pérez", 
                "salary": 5000000, "position": "Gerente General", "type": "INDEFINIDO", 
                "cc": cost_center, "transport": False
            },
            {
                "id_num": "1010101002", "first_name": "Ana", "surname": "Gómez", 
                "salary": 2500000, "position": "Analista Contable", "type": "INDEFINIDO", 
                "cc": cost_center, "transport": True
            },
            {
                "id_num": "1010101003", "first_name": "Carlos", "surname": "Rodríguez", 
                "salary": 1300000, "position": "Operario Planta 1", "type": "FIJO", 
                "cc": ops_center, "transport": True
            },
            {
                "id_num": "1010101004", "first_name": "Luisa", "surname": "Fernández", 
                "salary": 1300000, "position": "Operario Planta 2", "type": "FIJO", 
                "cc": ops_center, "transport": True
            },
            {
                "id_num": "1010101005", "first_name": "Pedro", "surname": "Martínez", 
                "salary": 1800000, "position": "Supervisor Planta", "type": "INDEFINIDO", 
                "cc": ops_center, "transport": True
            },
            {
                "id_num": "1010101006", "first_name": "María", "surname": "López", 
                "salary": 3000000, "position": "Líder Comercial", "type": "INDEFINIDO", 
                "cc": sale_center, "transport": False
            },
            {
                "id_num": "1010101007", "first_name": "Jorge", "surname": "Ramírez", 
                "salary": 1300000, "position": "Vendedor Junior", "type": "OBRA", 
                "cc": sale_center, "transport": True
            },
            {
                "id_num": "1010101008", "first_name": "Elena", "surname": "Torres", 
                "salary": 6000000, "position": "Desarrolladora Senior", "type": "INDEFINIDO", 
                "cc": cost_center, "transport": False
            },
            {
                "id_num": "1010101009", "first_name": "Sofía", "surname": "Vargas", 
                "salary": 1300000, "position": "Recepcionista", "type": "FIJO", 
                "cc": cost_center, "transport": True
            },
            {
                "id_num": "1010101010", "first_name": "Miguel", "surname": "Castro", 
                "salary": 1400000, "position": "Auxiliar Bodega", "type": "OBRA", 
                "cc": ops_center, "transport": True
            },
             {
                "id_num": "1010101011", "first_name": "Laura", "surname": "Méndez", 
                "salary": 2800000, "position": "Coordinadora RRHH", "type": "INDEFINIDO", 
                "cc": cost_center, "transport": True
            },
             {
                "id_num": "1010101012", "first_name": "Andrés", "surname": "Ruiz", 
                "salary": 900000, "position": "Aprendiz SENA", "type": "APRENDIZAJE", 
                "cc": cost_center, "transport": True
            },
        ]

        count = 0
        for emp_data in employees_data:
            # 1. Crear/Obtener Tercero
            third_party, created = ThirdParty.objects.get_or_create(
                identification_number=emp_data["id_num"],
                defaults={
                    "party_type": "EMPLEADO",
                    "person_type": 2, # Natural
                    "identification_type": "13", # CC
                    "first_name": emp_data["first_name"],
                    "surname": emp_data["surname"],
                    "email": f"{emp_data['first_name'].lower()}.{emp_data['surname'].lower()}@empresa.com",
                    "address": "Calle Falsa 123",
                    "phone": "3001234567",
                    "city_code": "76001",
                    "department_code": "76",
                    "country_code": "CO",
                    "postal_code": "760001",
                    "tax_regime": "49",
                    "fiscal_responsibilities": ["R-99-PN"],
                }
            )

            # 2. Crear Perfil de Empleado
            if not Employee.objects.filter(code=emp_data["id_num"]).exists():
                Employee.objects.create(
                    third_party=third_party,
                    code=emp_data["id_num"], # Usamos la cédula como código
                    contract_type=emp_data["type"],
                    start_date=date(2025, 1, 15),
                    base_salary=Decimal(emp_data["salary"]),
                    transport_allowance_eligible=emp_data["transport"],
                    health_entity="EPS SANITAS",
                    pension_entity="PROTECCION",
                    severance_entity="PORVENIR",
                    arl_entity="SURA",
                    risk_level=1,
                    cost_center=emp_data["cc"],
                    position=emp_data["position"],
                    is_active=True
                )
                count += 1
                self.stdout.write(self.style.SUCCESS(f"Empleado creado: {emp_data['first_name']} {emp_data['surname']}"))
            else:
                self.stdout.write(f"Empleado ya existe: {emp_data['first_name']}")

        self.stdout.write(self.style.SUCCESS(f"Proceso finalizado. Total empleados nuevos: {count}"))
