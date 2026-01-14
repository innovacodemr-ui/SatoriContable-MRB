import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.tenants.models import Client
from apps.support_docs.models import Supplier, DianResolution, SupportDocument
from apps.support_docs.services.xml_builder import SupportDocumentBuilder
from django.utils import timezone
from apps.support_docs.services.dian_sender import SupportDocumentSender

def run_test():
    print("--- INICIANDO TEST DE HUMO: DOCUMENTO SOPORTE ---")
    
    # 0. Crear Cliente (Tenant)
    client, _ = Client.objects.get_or_create(
        nit="900000000",
        defaults={
            "name": "MI EMPRESA SAS",
            "legal_name": "MI EMPRESA SAS",
            "address": "Calle Principal",
            "email": "info@miempresa.com",
        }
    )

    # 1. Crear Proveedor (Mock)
    # Usamos campos reales de ThirdParty: 
    # business_name, identification_number, identification_type, person_type, check_digit, city_code
    supplier, created = Supplier.objects.get_or_create(
        identification_number="10102020",
        defaults={
            "identification_type": "31", # NIT
            "check_digit": "5",
            "person_type": 2, # Natural
            "first_name": "PEDRO",
            "surname": "PEREZ",
            "business_name": "PEDRO PEREZ - CONTRATISTA", # Optional for person type 2 but good for safety
            "party_type": "PROVEEDOR",
            "city_code": "76001",
            "address": "CALLE 123 # 45-67",
            "department_code": "76",
            "phone": "3001234567",
            "email": "pedro@example.com",
            # "dv": "5" -> Incorrecto, es check_digit
            # "name": ... -> Incorrecto, usamos first_name/surname o business_name
        }
    )
    print(f"Proveedor: {supplier.get_full_name()} (Creado: {created})")

    # 2. Crear Resolución (Mock)
    resolution, _ = DianResolution.objects.get_or_create(
        resolution_number="18760000001",
        defaults={
            "client": client,
            "prefix": "DS",
            "start_date": "2024-01-01",
            "end_date": "2025-01-01",
            "from_number": 1,
            "to_number": 1000,
            "technical_key": "fc8eac422eba16e22ffd8c6f94b3f40a6e38162c" # Clave técnica hexadecimal de prueba
        }
    )
    print(f"Resolución: {resolution.resolution_number}")

    # 3. Crear Documento Soporte (DB Record)
    doc, created_doc = SupportDocument.objects.get_or_create(
        resolution=resolution,
        consecutive=1, 
        defaults={
            "client": client,
            "supplier": supplier,
            "issue_date": timezone.now().date(),
            "payment_due_date": timezone.now().date(),
            "payment_method": "1", # Contado
        }
    )
    print(f"Documento Soporte creado ID: {doc.id} (Nuevo: {created_doc})")

    # 4. Generar XML
    try:
        builder = SupportDocumentBuilder()
        xml_content = builder.build_xml(doc)
        
        # Guardar en archivo para inspección
        filename = "debug_support_doc.xml"
        with open(filename, "wb") as f:
            f.write(xml_content)
        
        print(f"✅ XML generado exitosamente: {filename}")
        print(f"Tamaño: {len(xml_content)} bytes")
        
        # Validar basic tags presence
        if b"Invoice" in xml_content and b"DIAN 2.1" in xml_content:
             print("Estructura básica UBL detectada.")
        else:
             print("⚠️ ADVERTENCIA: No se detectan etiquetas UBL estándar.")

    except Exception as e:
        print(f"❌ Error generando XML: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_test()
