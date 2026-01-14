import os
import django
from decimal import Decimal
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.accounting.models import Account, ThirdParty, JournalEntry
from apps.treasury.models import BankAccount, PaymentOut, PaymentOutDetail
from apps.electronic_events.models import ReceivedInvoice
from apps.treasury.services.treasury_service import TreasuryService
# Check if Client model is available or needed
try:
    from apps.tenants.models import Client
    has_tenant = True
except ImportError:
    has_tenant = False

def run_test():
    print("--- INICIANDO PRUEBA DE TESORERÍA: FLJO COMPLETO ---")
    
    # 1. Configurar Datos Previos
    print("\n[1/5] Verificando Datos Maestros...")
    
    # Proveedor
    supplier = ThirdParty.objects.filter(party_type='PROVEEDOR').first()
    if not supplier:
        print("❌ No se encontró proveedor. Ejecute load_demo_data.py primero.")
        return
    print(f"✅ Proveedor: {supplier.business_name} (NIT {supplier.identification_number})")

    # Banco
    bank = BankAccount.objects.first()
    if not bank:
        # Crear banco si no existe (load_demo_data no crea bancos explícitos, solo cuentas)
        # Necesitamos un BankAccount model instance
        bank_account_gl = Account.objects.get(code='111005')
        bank = BankAccount.objects.create(
            name='Cuenta Corriente Principal',
            account_number='987-654321',
            bank_name='Bancolombia',
            gl_account=bank_account_gl
        )
        print("✅ Banco Creado.")
    else:
        print(f"✅ Banco: {bank.bank_name} ({bank.account_number})")

    # Tenant (Cliente/Nosotros)
    client_obj = None
    if has_tenant:
        client_obj = Client.objects.first()
        if not client_obj:
            client_obj = Client.objects.create(
                name='MI EMPRESA SAS',
                nit='800123456',
                legal_name='MI EMPRESA SAS'
            )
    
    # 2. Crear Factura de Proveedor (Mock XML parsing)
    print("\n[2/5] Recibiendo Factura de Proveedor (Simulado)...")
    invoice_number = 'FE-999'
    invoice_total = Decimal('500000.00')
    
    # Check if exists to avoid dups
    invoice = ReceivedInvoice.objects.filter(invoice_number=invoice_number).first()
    if not invoice:
        invoice = ReceivedInvoice.objects.create(
            client=client_obj,
            issuer_nit=supplier.identification_number,
            issuer_name=supplier.business_name,
            invoice_number=invoice_number,
            cufe='cufe_dummy_123456789',
            issue_date=date.today(),
            subtotal_amount=invoice_total, # Simplificado sin IVA pa la prueba
            tax_amount=0,
            total_amount=invoice_total,
            xml_file='dummy.xml' 
        )
        print(f"✅ Factura Recibida creada: {invoice_number} por ${invoice_total}")
    else:
        print(f"✅ Factura Recibida existente: {invoice_number}")

    # 3. Crear Comprobante de Egreso (Borrador)
    print("\n[3/5] Creando Comprobante de Egreso (Borrador)...")
    payment = PaymentOut.objects.create(
        payment_date=date.today(),
        third_party=supplier.business_name,
        bank_account=bank,
        payment_method='TRANSFERENCIA',
        total_amount=invoice_total,
        notes='Pago Pruebas Drill Test',
        status='DRAFT'
    )
    
    # Detalles (Qué facturas paga)
    PaymentOutDetail.objects.create(
        payment_out=payment,
        invoice=invoice,
        amount_paid=invoice_total
    )
    print(f"✅ Comprobante CE-{payment.consecutive} creado en Borrador.")

    # 4. Contabilizar (El Disparo Real)
    print("\n[4/5] CONTABILIZANDO (Ejecutando TreasuryService)...")
    try:
        entry = TreasuryService.post_payment(payment.id)
        print(f"✅ ÉXITO. Asiento Contable Generado: {entry.number}")
    except Exception as e:
        print(f"❌ FALLÓ LA CONTABILIZACIÓN: {e}")
        import traceback
        traceback.print_exc()
        return

    # 5. Verificar Resultados
    print("\n[5/5] Auditoría del Asiento Contable:")
    print(f"  Documento: {entry.number} | Fecha: {entry.date} | Estado: {entry.status}")
    print("  -------------------------------------------------------------")
    print("  {:^10} | {:^40} | {:^12} | {:^12}".format("CUENTA", "DESCRIPCIÓN", "DÉBITO", "CRÉDITO"))
    print("  -------------------------------------------------------------")
    for line in entry.lines.all():
        print("  {:^10} | {:<40} | {:>12,.2f} | {:>12,.2f}".format(
            line.account.code, 
            line.description[:40], 
            line.debit, 
            line.credit
        ))
    print("  -------------------------------------------------------------")
    
    # Validación simple
    total_debits = sum(l.debit for l in entry.lines.all())
    total_credits = sum(l.credit for l in entry.lines.all())
    
    if total_debits == total_credits == invoice_total:
         print("\n✅ PRUEBA SUPERADA: Partida Doble Perfecta.")
    else:
         print(f"\n⚠️ ALERTA: Diferencia en sumas iguales ({total_debits} vs {total_credits})")

if __name__ == '__main__':
    run_test()
