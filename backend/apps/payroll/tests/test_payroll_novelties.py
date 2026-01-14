from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import date, timedelta
from apps.payroll.models import NoveltyType, Employee, EmployeeNovelty
from apps.accounting.models import ThirdParty
from django.contrib.auth.models import User

class PayrollNoveltiesTests(APITestCase):
    
    def setUp(self):
        # 0. Crear Usuario y Autenticar
        self.user = User.objects.create_user(username='admin', password='password123')
        self.client.force_authenticate(user=self.user)

        # 1. Crear Tercero (Corregido con campos reales del modelo)
        self.third_party = ThirdParty.objects.create(
            party_type="EMPLEADO",
            person_type=2, # Persona Natural
            first_name="Juan",
            surname="Perez",
            identification_number="123456789",
            identification_type="13", # CC
            is_active=True
        )
        # 2. Crear Empleado
        self.employee = Employee.objects.create(
            third_party=self.third_party,
            code="EMP_001",
            contract_type="INDEFINIDO",
            start_date=date(2026, 1, 1),
            base_salary=2000000,
            health_entity="EPS Sanitas",
            pension_entity="Porvenir",
            severance_entity="Porvenir",
            arl_entity="Sura",
            position="Gerente"
        )
        
        # 3. Crear Tipos de Novedad
        self.vac_type = NoveltyType.objects.create(
            code="VAC",
            name="Vacaciones",
            dian_type="VAC",
            payroll_payment_percentage=1.00
        )
        self.ige_type = NoveltyType.objects.create(
            code="IGE_66",
            name="Incapacidad General",
            dian_type="IGE",
            payroll_payment_percentage=0.6667
        )

        self.url = '/api/payroll/employee-novelties/'

    def test_create_novelty_happy_path(self):
        """
        Escenario 1: Creación exitosa (Happy Path).
        Vacaciones del 1 al 15 de Agosto.
        """
        # Crear archivo dummy
        file_content = b"Contenido del PDF de soporte"
        attachment = SimpleUploadedFile("soporte_vacaciones.pdf", file_content, content_type="application/pdf")

        data = {
            "employee": self.employee.id,
            "novelty_code": "VAC",
            "start_date": "2026-08-01",
            "days": 15,
            "attachment": attachment
        }

        response = self.client.post(self.url, data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['days'], 15)
        self.assertEqual(response.data['novelty_name'], "Vacaciones")
        
        # Verificar fecha fin calculada: 1 + 15 - 1 = 15
        self.assertEqual(response.data['end_date'], "2026-08-15")
        
        # Verificar persistencia y ruta de archivo dinámica
        novelty = EmployeeNovelty.objects.get(id=response.data['id'])
        self.assertEqual(novelty.end_date, date(2026, 8, 15))
        # Ruta esperada: novelties/(AÑO)/(MES)/EMP_(CÓDIGO)/archivo
        expected_path_part = f"novelties/2026/08/EMP_{self.employee.code}/soporte_vacaciones"
        self.assertTrue(expected_path_part in novelty.attachment.name.replace("\\", "/"))

    def test_create_novelty_overlap_error(self):
        """
        Escenario 2: Error por solapamiento (Overlap Conflict).
        Intentar crear Incapacidad el 5 de Agosto cuando ya hay Vacaciones (1-15 Ago).
        """
        # Precondición: Crear la novedad de Vacaciones (directo en DB o vía cliente)
        EmployeeNovelty.objects.create(
            employee=self.employee,
            novelty_type=self.vac_type,
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 15),
            days=15
        )

        # Intento de colisión
        data = {
            "employee": self.employee.id,
            "novelty_code": "IGE_66",
            "start_date": "2026-08-05", # Cae dentro del rango 1-15
            "days": 3 # Terminaría el 7
        }

        response = self.client.post(self.url, data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        error_msg = str(response.data)
        self.assertIn("El empleado ya tiene una novedad registrada en estas fechas", error_msg)
        self.assertIn("Vacaciones", error_msg)

    def test_novelty_code_resolution(self):
        """
        Escenario 3: Resolución de Código (Code Resolution).
        Enviar 'IGE_66' y verificar que se asocia al NoveltyType correcto.
        """
        data = {
            "employee": self.employee.id,
            "novelty_code": "IGE_66",
            "start_date": "2026-09-01",
            "days": 2
        }

        response = self.client.post(self.url, data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        created_id = response.data['id']
        novelty = EmployeeNovelty.objects.get(id=created_id)
        
        # Verificar que el Type ID corresponde al objeto IGE_66 creado en setUp
        self.assertEqual(novelty.novelty_type.id, self.ige_type.id)
        self.assertEqual(novelty.novelty_type.code, "IGE_66")
