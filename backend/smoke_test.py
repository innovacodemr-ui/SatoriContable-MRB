import os
import django
from decimal import Decimal
from django.utils import timezone

# Setup handled by manage.py shell usually, but good for standalone if needed properties set
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_dev')
# django.setup()

from apps.accounting.models import AccountingTemplate, AccountingTemplateLine, Account, AccountingDocumentType, AccountClass, AccountGroup
from apps.accounting.services.accounting_engine import AccountingEngine
from apps.electronic_events.models import ReceivedInvoice
from apps.tenants.models import Client
from apps.support_docs.models import Supplier

def run_test():
    print(">>> 🧪 INICIANDO SMOKE TEST: MOTOR CONTABLE SATORI <<<")

    # 1. PREPARACIÓN DE INFRAESTRUCTURA (PUC)
    print("\n[1/5] Estructurando el PUC...")
    
    # Clase 5 - Gastos
    class_5, _ = AccountClass.objects.get_or_create(code='5', defaults={'name': 'Gastos', 'nature': 'DEBITO'})
    group_51, _ = AccountGroup.objects.get_or_create(code='51', account_class=class_5, defaults={'name': 'Operacionales de Administración'})
    
    # Clase 2 - Pasivo
    class_2, _ = AccountClass.objects.get_or_create(code='2', defaults={'name': 'Pasivo', 'nature': 'CREDITO'})
    group_24, _ = AccountGroup.objects.get_or_create(code='24', account_class=class_2, defaults={'name': 'Impuestos Gravámenes y Tasas'})
    group_23, _ = AccountGroup.objects.get_or_create(code='23', account_class=class_2, defaults={'name': 'Cuentas por Pagar'})

    # Cuentas
    cta_gasto, _ = Account.objects.get_or_create(
        code='519505', 
        defaults={
            'name': 'Útiles y Papelería', 
            'nature': 'DEBITO',
            'account_group': group_51,
            'level': 6,
            'account_type': 'GASTO',
            'allows_movement': True
        }
    )
    
    cta_iva, _ = Account.objects.get_or_create(
        code='2408', 
        defaults={
            'name': 'IVA Descontable', 
            'nature': 'DEBITO', # IVA descontable se debita
            'account_group': group_24,
            'level': 4,
            'account_type': 'PASIVO',
            'allows_movement': True
        }
    )
    
    cta_cxp, _ = Account.objects.get_or_create(
        code='2335', 
        defaults={
            'name': 'Costos y Gastos por Pagar', 
            'nature': 'CREDITO',
            'account_group': group_23,
            'level': 4,
            'account_type': 'PASIVO',
            'allows_movement': True
        }
    )
    print(f"    ✅ Cuentas verificadas: {cta_gasto}, {cta_iva}, {cta_cxp}")

    # 2. CONFIGURACIÓN DE PLANTILLAS
    print("\n[2/5] Configurando Plantilla Contable...")
    doctype, _ = AccountingDocumentType.objects.get_or_create(code='FC', defaults={'name': 'Factura Compra'})
    
    template, _ = AccountingTemplate.objects.get_or_create(name="Compra Papelería TEST", document_type=doctype, active=True)
    
    # Limpiar líneas previas si existen para no duplicar en reintentos
    template.lines.all().delete()

    # Línea 1: Gasto (100% del Subtotal)
    AccountingTemplateLine.objects.create(
        template=template, account=cta_gasto, 
        nature='DEBITO', calculation_method='PERCENTAGE_OF_SUBTOTAL', value=100,
        description_template="Gasto Papelería Factura {numero}"
    )
    # Línea 2: IVA (Automático basado en el tax_amount del documento)
    AccountingTemplateLine.objects.create(
        template=template, account=cta_iva, 
        nature='DEBITO', calculation_method='PERCENTAGE_OF_TAX', value=100,
         description_template="IVA Factura {numero}"
    )
    # Línea 3: CxP (El resto/Plug para cuadrar)
    AccountingTemplateLine.objects.create(
        template=template, account=cta_cxp, 
        nature='CREDITO', calculation_method='PLUG', value=0,
         description_template="CxP Proveedor {tercero}"
    )
    print(f"    ✅ Plantilla '{template.name}' configurada con 3 líneas.")

    # 3. CREACIÓN DEL DOCUMENTO ORIGEN
    print("\n[3/5] Simulando Recepción de Factura...")
    client, _ = Client.objects.get_or_create(
        nit='900000000', 
        defaults={'name': 'Empresa Demo', 'legal_name': 'Empresa Demo SAS'}
    ) # Tenant dummy
    
    # Proveedor dummy para el asiento
    supplier, _ = Supplier.objects.get_or_create(
        identification_number="900123456",
        defaults={'business_name': 'Papelería Satori SAS', 'party_type': 'PROVEEDOR', 'person_type': 1}
    )

    # Factura
    try:
        factura_fake = ReceivedInvoice.objects.get(invoice_number="SETT-TEST-001")
        print("    ℹ️ Usando factura existente SETT-TEST-001")
    except ReceivedInvoice.DoesNotExist:
        factura_fake = ReceivedInvoice.objects.create(
            client=client,
            issuer_nit=supplier.identification_number,
            issuer_name=supplier.business_name,
            invoice_number="SETT-TEST-001",
            cufe="cufe_dummy_test_123456789",
            issue_date=timezone.now().date(),
            total_amount=Decimal("119000.00"),
            subtotal_amount=Decimal("100000.00"),
            tax_amount=Decimal("19000.00"),
            xml_file="dummy.xml"
        )
        print("    ✅ Factura SETT-TEST-001 creada.")
    
    # 4. EJECUCIÓN DEL MOTOR
    print("\n[4/5] 🔥 IGNITION: Ejecutando AccountingEngine...")
    try:
        entry = AccountingEngine.generate_entry(factura_fake, template, supplier)
        print(f"    ✅ Asiento Generado: {entry}")
        print(f"    Estado: {entry.status}")
        print(f"    Débitos Totales: {entry.get_total_debit()}")
        print(f"    Créditos Totales: {entry.get_total_credit()}")
        
        print("\n[5/5] 🧐 INSPECCIÓN DE DETALLE:")
        for line in entry.lines.all().order_by('line_number'):
            print(f"    Línea {line.line_number} | Cuenta: {line.account.code} | {line.description} | Débito: {line.debit:,.2f} | Crédito: {line.credit:,.2f}")
        
        # Validaciones finales
        if entry.is_balanced():
            print("\n🎉 RESULTADO: ÉXITO. El asiento cuadra perfectamente.")
        else:
            print("\n❌ RESULTADO: FALLO. El asiento está desbalanceado.")

    except Exception as e:
        print(f"\n💥 ERROR FATAL EN EL MOTOR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_test()
