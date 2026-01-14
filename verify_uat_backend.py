import requests
import os
import sys
from pathlib import Path
import django
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

# Setup Django standalone to access models directly for Forensic Test
# Use absolute path relative to this script
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR / 'backend'))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.payroll.models import EmployeeNovelty, Employee, NoveltyType
from django.contrib.auth.models import User
from rest_framework.test import APIClient

def run_backend_uat():
    print("--- INICIANDO PROTOCOLO DE VALIDACIÓN BACKEND (UAT AUTOMATIZADO) ---")

    # CLEANUP: Borrar datos previos para prueba limpia
    EmployeeNovelty.objects.all().delete()
    print("[RESET] Base de datos de novedades limpiada.")

    # PREPARACIÓN: Obtener datos base
    try:
        # Create user if not exists for auth
        if not User.objects.filter(username='admin').exists():
             User.objects.create_user(username='admin', password='password123', email='admin@example.com')
        
        # Ensure Employee exists
        if not Employee.objects.filter(code="EMP_002").exists():
             print("[WARN] EMP_002 No existe, creando dummy...")
             from datetime import date
             from apps.accounting.models import ThirdParty
             tp, _ = ThirdParty.objects.get_or_create(
                 identification_number="987654321",
                 defaults={"party_type": "EMPLEADO", "person_type": 2, "first_name": "Ana", "surname": "Gomez", "identification_type": "13"}
             )
             Employee.objects.create(
                 third_party=tp, code="EMP_002", contract_type="INDEFINIDO",
                 start_date=date(2025,1,1), base_salary=3000000,
                 health_entity="EPS", pension_entity="AFP", severance_entity="CES", arl_entity="ARL", position="Dev"
             )
             
        emp = Employee.objects.get(code="EMP_002") # Ana Gómez
        print(f"[DATA] Empleado encontrado: {emp}")
    except Exception as e:
        print(f"[ERROR] Setup falló: {e}")
        return

    admin_user = User.objects.get(username='admin')
    client = APIClient()
    client.force_authenticate(user=admin_user)
    
    # 1. PRUEBA DE FUEGO (PARTE A): Registro Exitoso
    print("\n>>> EJECUTANDO: Registro de Incapacidad (Happy Path)...")
    file_content = b"Fake PDF Content"
    file = SimpleUploadedFile("incapacidad.pdf", file_content, content_type="application/pdf")
    
    data = {
        "employee": emp.id,
        "novelty_code": "IGE_66",
        "start_date": "2026-08-01",
        "days": 3,
        "attachment": file
    }
    
    # Need to check if IGE_66 exists
    if not NoveltyType.objects.filter(code="IGE_66").exists():
         NoveltyType.objects.create(code="IGE_66", name="Incapac", dian_type="IGE", payroll_payment_percentage=0.6667)

    response = client.post('/api/payroll/employee-novelties/', data, format='multipart')
    
    if response.status_code == 201:
        print(f"✅ ÉXITO: Novedad creada. ID: {response.data.get('id')}")
    else:
        print(f"❌ FALLO CREACIÓN: {response.status_code} - {response.data}")
        return

    # 2. PRUEBA DE FUEGO (PARTE B): Solapamiento
    print("\n>>> EJECUTANDO: Intento de Solapamiento (Debe fallar)...")
    # Intentamos meter vacaciones en medio de la incapacidad (1 al 3 de Agosto)
    # Check if VAC exists
    if not NoveltyType.objects.filter(code="VAC").exists():
         NoveltyType.objects.create(code="VAC", name="Vacaciones", dian_type="VAC", payroll_payment_percentage=1.0)

    data_conflict = {
        "employee": emp.id,
        "novelty_code": "VAC", # Vacaciones
        "start_date": "2026-08-02", # Colisiona
        "days": 5
    }
    
    response_conflict = client.post('/api/payroll/employee-novelties/', data_conflict, format='multipart')
    
    if response_conflict.status_code == 400:
        print("✅ ÉXITO: El sistema bloqueó el solapamiento correctamente.")
        print(f"   Mensaje recibido: {response_conflict.data}")
    else:
        print(f"❌ FALLO VALIDACIÓN: Status: {response_conflict.status_code}")

    # 3. PRUEBA FORENSE (Integridad de Archivos)
    print("\n>>> EJECUTANDO: Verificación Forense de Archivos...")
    try:
        novelty_id = response.data.get('id')
        novelty = EmployeeNovelty.objects.get(id=novelty_id)
        if novelty.attachment:
            file_path = novelty.attachment.path
            
            if os.path.exists(file_path):
                print(f"✅ ÉXITO: Archivo encontrado físicamente en el disco.")
                print(f"   Ruta: {file_path}")
                print(f"   Tamaño: {os.path.getsize(file_path)} bytes")
            else:
                print(f"❌ FALLO: El registro existe en BD pero el archivo no está en disco en {file_path}")
        else:
            print("⚠️ AVISO: No se creó attachment.")
            
    except Exception as e:
        print(f"❌ ERROR FORENSE: {e}")

    print("\n--- PROTOCOLO FINALIZADO ---")

if __name__ == "__main__":
    run_backend_uat()
