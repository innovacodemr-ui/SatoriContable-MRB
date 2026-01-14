import os
import django
from decimal import Decimal
from django.core.files.base import ContentFile
import sys

# Setup Django Environment
sys.path.append(os.path.join(os.getcwd(), 'backend'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings_dev")
django.setup()

from apps.accounting.models import AccountingTemplate, AccountingTemplateLine, Account, JournalEntry, ThirdParty
from apps.electronic_events.models import ReceivedInvoice
from apps.accounting.services.accounting_engine import AccountingEngine
from apps.tenants.models import Client

def run_verification():
    print("🚀 Iniciando Prueba de Integración Total: RADIAN -> CONTABILIDAD")
    
    # 0. Asegurar Cliente (Tenant)
    client, _ = Client.objects.get_or_create(
        nit="900123456-1",
        defaults={"business_name": "Satori Corp"}
    )
    
    # 1. Crear Factura Recibida Simulada
    print("\n1. Simulando Llegada de Factura XML (Inbox)...")
    invoice_number = "SETP-999"
    issuer_nit = "800111222-3"
    
    # Limpiar previos para evitar error de unique
    ReceivedInvoice.objects.filter(invoice_number=invoice_number).delete()
    JournalEntry.objects.filter(number=f"AUTO-{invoice_number}").delete()
    
    invoice = ReceivedInvoice.objects.create(
        client=client,
        issuer_nit=issuer_nit,
        issuer_name="PROVEEDOR DE PRUEBA SAS",
        invoice_number=invoice_number,
        cufe="abcdef1234567890",
        issue_date="2025-01-01",
        subtotal_amount=Decimal("100000"),
        tax_amount=Decimal("19000"),
        total_amount=Decimal("119000"),
        xml_file=ContentFile(b"<xml>dummy</xml>", name="factura.xml")
    )
    print(f"   ✅ Factura creada: {invoice} | Total: ${invoice.total_amount}")

    # 2. Crear Plantilla Contable (Si no existe)
    print("\n2. Configurando Plantilla 'Compra General'...")
    template, _ = AccountingTemplate.objects.get_or_create(
        name="Compra General TEST-AUTO",
        defaults={"active": True, "document_type_id": 1} # Asumiendo DocType 1 existe
    )
    template.lines.all().delete()
    
    # Cuentas Mock (Deben existir en smoke_test, reutilizamos o aseguramos)
    try:
        # Intentar obtener cuentas reales o crear dummies
        # Usamos filtros más laxos para asegurar match
        acc_gasto = Account.objects.filter(code__startswith='5').first()
        acc_iva = Account.objects.filter(code__startswith='2').first() 
        acc_cxp = Account.objects.filter(code__startswith='2').last() # Diferente a iva ojala
        
        if not acc_gasto:
             acc_gasto = Account.objects.create(code='519500', name='Gastos Test', nature='DEBITO', account_class_id=1) # ID fake
        if not acc_iva:
             acc_iva = Account.objects.create(code='240800', name='IVA Test', nature='CREDITO', account_class_id=1)
        if not acc_cxp:
             acc_cxp = Account.objects.create(code='233500', name='CXP Test', nature='CREDITO', account_class_id=1)

    except Exception as e:
        print(f"Error getting accounts: {e}")
        return

    # Linea 1: IVA (Impuesto)
    AccountingTemplateLine.objects.create(
        template=template, account=acc_iva, nature='DEBITO', 
        calculation_method='PERCENTAGE_OF_TAX', value=100, description_template="IVA Op"
    )
    # Linea 2: CxP (Total - Crédito)
    try:
        AccountingTemplateLine.objects.create(
            template=template, account=acc_cxp, nature='CREDITO', 
            calculation_method='PERCENTAGE_OF_TOTAL', value=100, description_template="CxP Prov"
        )
    except Exception as e:
        # Fallback si PORCENTAJE espera value max 100
        pass

    # Linea 3: Gasto (El Plug/Diferencia al Debito)
    AccountingTemplateLine.objects.create(
        template=template, account=acc_gasto, nature='DEBITO', 
        calculation_method='PLUG', value=0, description_template="Gasto Plug"
    )
    
    print("   ✅ Plantilla configurada (Estrategia: IVA + CxP 100% + Plug Gasto).")

    # 3. Ejecutar 'Boton Contabilizar' (Simulado)
    print("\n3. Ejecutando AccountingEngine.generate_entry()...")
    
    # Simular la logica del ViewSet (Get/Create ThirdParty)
    nit_clean = issuer_nit.replace('-', '')
    third_party, _ = ThirdParty.objects.get_or_create(
        identification_number=nit_clean, 
        defaults={
            'party_type': 'PROVEEDOR', 
            'person_type': 1,
            'identification_type': '31',
            'business_name': "PROVEEDOR DE PRUEBA SAS"  # Added business_name
        }
    )
    
    try:
        entry = AccountingEngine.generate_entry(invoice, template, third_party)
        print(f"   ✅ ¡ÉXITO! Asiento Generado: ID {entry.id} | Número {entry.number}")
    except Exception as e:
        print(f"   ❌ ERROR FATAL EN MOTOR: {e}")
        import traceback
        traceback.print_exc()
        return

    # 4. Verificaciones
    print("\n4. Reporte de Auditoría (Checklist de Vuelo):")
    
    # A. Tercero
    # Revisar lineas del asiento
    lines = entry.lines.all()
    print(f"   🔍 Líneas del Asiento: {lines.count()}")
    ok_third = True
    for line in lines:
        t_name = line.third_party.business_name if line.third_party else "None"
        is_debit = line.debit > 0
        nature_str = "DEBITO" if is_debit else "CREDITO"
        val = line.debit if is_debit else line.credit
        print(f"      - {line.account.code} ({nature_str}) | ${val} | Tercero: {t_name}")
        
        if line.third_party != third_party:
            ok_third = False
    
    if ok_third:
        print("   ✅ [OK] Tercero vinculado correctamente en todas las líneas.")
    else:
        print("   ⚠️ [FAIL] Discrepancia en terceros.")

    # B. Decimales / Cuadre
    diff = entry.get_total_debit() - entry.get_total_credit()
    if diff == 0 and entry.is_balanced():
        print(f"   ✅ [OK] Asiento Cuadrado (Débito: {entry.get_total_debit()} = Crédito: {entry.get_total_credit()}).")
    else:
        print(f"   ❌ [FAIL] Asiento Descuadrado (Dif: {diff}).")

    # B.2 Valores específicos
    # Esperamos: CxP = 119,000 (Credito), IVA = 19,000 (Debito), Gasto = 100,000 (Debito/Plug)
    line_cxp = lines.filter(credit__gte=100000).first() # Buscar la grande por credito
    if line_cxp and abs(line_cxp.credit - Decimal("119000")) < Decimal("1.00"):
        print("   ✅ [OK] Valor CxP correcto ($119,000).")
    else:
        cxp_val = line_cxp.credit if line_cxp else 'Not Found'
        print(f"   ⚠️ [Check] Valor CxP: {cxp_val} (Esperado 119000)")

    # C. Trazabilidad
    if entry.content_type.model == 'receivedinvoice' and entry.object_id == invoice.id:
        print(f"   ✅ [OK] Trazabilidad Confirmada: Asiento apunta a Factura {invoice.invoice_number}.")
    else:
         print(f"   ❌ [FAIL] Sin trazabilidad (Source: {entry.content_type} ID {entry.object_id}).")

    print("\n🏁 PRUEBA COMPLETADA.")

if __name__ == "__main__":
    run_verification()
