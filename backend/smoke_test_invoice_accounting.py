import os
import django
import sys
from decimal import Decimal
from datetime import date

# Setup Django environment
sys.path.append(os.path.join(os.getcwd(), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from rest_framework.test import APIRequestFactory, force_authenticate
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from apps.invoicing.models import Resolution, Item, Invoice
from apps.accounting.models import ThirdParty, JournalEntry
from apps.invoicing.views import InvoiceViewSet

def verify_invoice_accounting():
    print("--- INICIANDO OPERACIÓN 'PRIMERA VENTA' (Simulación) ---")
    
    User = get_user_model()
    user, _ = User.objects.get_or_create(username='test_admin', defaults={'email': 'admin@satori.com', 'is_staff': True})
    
    # 1. Munición (Producto)
    item, created = Item.objects.get_or_create(
        code='CONS-GOLD',
        defaults={
            'description': 'Consultoría Satori Gold',
            'unit_price': Decimal('1000000'),
            'type': 'SERVICIO',
            'tax_type': 'IVA_19'
        }
    )
    print(f"1. Producto: {item.description} - Precio: ${item.unit_price} - IVA: {item.tax_type}")
    
    # 2. Infraestructura (Cliente y Resolución)
    customer, _ = ThirdParty.objects.get_or_create(
        identification_number='999999999',
        defaults={
            'party_type': 'CLIENTE',
            'person_type': 1,  # 1: Juridica
            'identification_type': '31', # NIT
            'business_name': 'Cliente Test Ltda',
            'email': 'test@cliente.com'
        }
    )
    
    resolution = Resolution.objects.first()
    if not resolution:
        print("❌ Error: No hay resoluciones activas para la prueba.")
        return

    # 3. El Disparo (Crear Factura via API View)
    data = {
        "resolution": resolution.id,
        "customer": customer.id,
        "payment_due_date": str(date.today()),
        "payment_term": "CONTADO",
        "notes": "Prueba de Integración Contable",
        "lines": [
            {
                "item": item.id,
                "description": item.description,
                "quantity": 1,
                "unit_price": float(item.unit_price),
                "tax_rate": 19
            }
        ],
        "status": "POSTED"
    }
    
    factory = APIRequestFactory()
    view = InvoiceViewSet.as_view({'post': 'create'})
    request = factory.post('/api/invoicing/invoices/', data, format='json')
    force_authenticate(request, user=user)
    
    print("\nEnviando fuego (Creando Factura)...")
    response = view(request)
    
    if response.status_code != 201:
        print(f"❌ Error al crear factura: {response.data}")
        return
        
    invoice_id = response.data['id']
    invoice_total = response.data['total']
    invoice_tax = response.data['tax_total']
    
    print(f"✅ Factura Creada ID: {invoice_id}")
    print(f"   Subtotal: ${response.data['subtotal']}")
    print(f"   Impuestos: ${invoice_tax} (Esperado: 190000.00)")
    print(f"   Total: ${invoice_total} (Esperado: 1190000.00)")
    
    # SIMULACIÓN DE APROBACIÓN (POSTING)
    # Como el API crea en Borrador, simulamos el click de "Confirmar/Contabilizar"
    print("\n--- SIMULANDO APROBACIÓN (POSTING) ---")
    inv = Invoice.objects.get(id=invoice_id)
    inv.status = 'POSTED'
    inv.save() # Esto debería disparar el Signal
    print("✅ Factura aprobada y guardada.")

    # 4. El Informe Forense (Buscar Asiento Contable)
    print("\n--- INFORME FORENSE CONTABLE ---")
    
    # Buscamos el asiento enlazado específicamente a esta factura
    try:
        ct = ContentType.objects.get_for_model(Invoice)
        entry = JournalEntry.objects.filter(content_type=ct, object_id=invoice_id).first()
        
        if entry:
            print(f"🎉 ESCENARIO A (EL MILAGRO): ¡Hay coincidencia contable! (Entry ID: {entry.id})")
            print(f"   Descripción: {entry.description}")
            print("   Líneas:")
            for line in entry.lines.all():
                print(f"   - Cuenta: {line.account.code} | Débito: ${line.debit:,.2f} | Crédito: ${line.credit:,.2f}")
                
            # Verificar balance
            total_debit = sum(line.debit for line in entry.lines.all())
            total_credit = sum(line.credit for line in entry.lines.all())
            if total_debit == total_credit == Decimal(str(invoice_total)):
                 print(f"   ✅ Balance Perfecto: ${total_debit:,.2f}")
            else:
                 print(f"   ⚠️ Desbalance: DB ${total_debit} vs CR ${total_credit}")
        else:
            print("❌ No se encontró ningún asiento contable vinculado a esta factura.")
            print("   Diagnóstico: Escenario B (Silencio Contable).")
            
    except Exception as e:
        print(f"❌ Error buscando asiento: {e}")

if __name__ == "__main__":
    verify_invoice_accounting()
