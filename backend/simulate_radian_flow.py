import os
import django
import sys
import json

# Setup Django Environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from rest_framework.test import APIRequestFactory
from apps.electronic_events.views import SendEventView
from apps.electronic_events.models import ReceivedInvoice, InvoiceEvent
from apps.tenants.models import Client
from django.core.files.uploadedfile import SimpleUploadedFile

def run_simulation():
    print("🚀 INICIANDO SIMULACIÓN DE COMBATE RADIAN (DRILL TEST)...")
    
    # 1. Preparar Terreno (Limpiar y Crear Datos Dummy)
    print("\n[Paso 0] Preparando datos de prueba...")
    
    # Asegurar Cliente
    client, created = Client.objects.get_or_create(
        nit='900000000-1',
        defaults={
            'name': 'Empresa de Prueba Satori',
            'legal_name': 'Empresa de Prueba Satori SAS',
            'dian_test_set_id': 'xxxx-xxxx-xxxx', 
            'tax_regime': 'COMUN'
        }
    )
    # Mockear Certificado (FileField necesita un archivo dummy si la vista lo abre)
    # La vista hace: if not client.dian_certificate: return Error
    # Vamos a asignar un archivo dummy.
    if not client.dian_certificate:
         client.dian_certificate = SimpleUploadedFile("cert.p12", b"fake_cert_content")
         client.certificate_password_encrypted = "fake_encrypted_pass" 
         client.save()
    
    # Crear Factura Dummy
    invoice, _ = ReceivedInvoice.objects.get_or_create(
        cufe='de3c7b...fake_cufe...12345',
        defaults={
            'client': client,
            'issuer_nit': '800123456',
            'issuer_name': 'Proveedor Hostil Ltda',
            'invoice_number': 'SETT-999',
            'total_amount': 1500000.00,
            'issue_date': '2025-01-01',
            'xml_file': SimpleUploadedFile("dummy.xml", b"<xml>Dummy</xml>")
        }
    )
    print(f"   > Factura creada/recuperada: {invoice.invoice_number} (ID: {invoice.id})")
    
    # Limpiar eventos previos si existen (por rehacer pruebas)
    invoice.events.all().delete()
    # Reset dian_status to simulate clean slate
    invoice.save()
    
    factory = APIRequestFactory()
    view = SendEventView.as_view()
    
    # Simular usuario autenticado (si es requerido por DRF permission_classes)
    # Por defecto, APIView puede requerir auth. 
    # Force authentication is easier with SimulationView or just mock request.user
    from rest_framework.test import force_authenticate
    from django.contrib.auth.models import User
    
    user, _ = User.objects.get_or_create(username='test_commander')
    
    # ==========================================
    # PASO 1: EVENTO 030 (ACUSE DE RECIBO)
    # ==========================================
    print("\n[Paso 1] Disparando Evento 030 (Acuse de Recibo)...")
    req_030 = factory.post(
        f'/api/radian/send-event/{invoice.id}/', 
        {'event_code': '030'}, 
        format='json'
    )
    force_authenticate(req_030, user=user)
    resp_030 = view(req_030, invoice_id=invoice.id)
    
    if resp_030.status_code == 200:
        print("   ✅ [ÉXITO] Acuse de Recibo confirmado.")
        print(f"   > Mensaje: {resp_030.data['message']}")
        print(f"   > Semáforo Backend: {[e['event_code'] for e in resp_030.data['invoice']['events']]}")
    else:
        print(f"   ❌ [FALLO] Error en Acuse: {resp_030.data}")
        return

    # ==========================================
    # PASO 2: EVENTO 032 (RECIBO DEL BIEN)
    # ==========================================
    print("\n[Paso 2] Disparando Evento 032 (Recibo del Bien)...")
    req_032 = factory.post(
        f'/api/radian/send-event/{invoice.id}/', 
        {'event_code': '032'}, 
        format='json'
    )
    force_authenticate(req_032, user=user)
    resp_032 = view(req_032, invoice_id=invoice.id)
    
    if resp_032.status_code == 200:
        print("   ✅ [ÉXITO] Bienes Recibidos confirmados.")
        print(f"   > Mensaje: {resp_032.data['message']}")
    else:
        print(f"   ❌ [FALLO] Error en Recibo Bien: {resp_032.data}")
        return

    # ==========================================
    # PASO 3: EVENTO 033 (ACEPTACIÓN EXPRESA)
    # ==========================================
    print("\n[Paso 3] Disparando Evento 033 (Aceptación Expresa)...")
    req_033 = factory.post(
        f'/api/radian/send-event/{invoice.id}/', 
        {'event_code': '033'}, 
        format='json'
    )
    force_authenticate(req_033, user=user)
    resp_033 = view(req_033, invoice_id=invoice.id)
    
    if resp_033.status_code == 200:
        print("   ✅ [ÉXITO] Factura Aceptada Expresamente.")
        print(f"   > Mensaje: {resp_033.data['message']}")
    else:
        print(f"   ❌ [FALLO] Error en Aceptación: {resp_033.data}")
        return

    print("\n🎉 MISIÓN CUMPLIDA. La secuencia completa (030 -> 032 -> 033) es operativa.")

if __name__ == '__main__':
    run_simulation()
