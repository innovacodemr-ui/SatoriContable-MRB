import os
import django
import random
from datetime import datetime
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.accounting.models import (
    Account, AccountClass, AccountGroup, ThirdParty,
    AccountingDocumentType, AccountingTemplate, AccountingTemplateLine,
    JournalEntry, JournalEntryLine
)

def create_accounts():
    print(">>> 1. Creating Accounts Structure...")
    # Helper to create structure
    def ensure_account(code, name, nature, type, parent_code=None):
        # Determine Group and Class from code
        class_code = code[0]
        group_code = code[:2]
        
        # Class
        acc_class, _ = AccountClass.objects.get_or_create(
            code=class_code, defaults={'name': f'CLASE {class_code}', 'nature': nature}
        )
        
        # Group
        acc_group, _ = AccountGroup.objects.get_or_create(
            code=group_code, defaults={
                'name': f'GRUPO {group_code}', 
                'account_class': acc_class,
                #'nature': nature # AccountGroup no tiene nature
            }
        )
        
        # Account
        acc, created = Account.objects.get_or_create(
            code=code,
            defaults={
                'name': name,
                'account_group': acc_group,
                'nature': nature,
                'account_type': type,
                'level': len(code),
                'allows_movement': True
            }
        )
        if created:
            print(f"Created Account: {code} - {name}")
        return acc

    # Assets
    ensure_account('110505', 'Caja General', 'DEBITO', 'ACTIVO')
    ensure_account('130505', 'Clientes Nacionales', 'DEBITO', 'ACTIVO')
    
    # Liabilities
    ensure_account('233525', 'Honorarios', 'CREDITO', 'PASIVO')
    ensure_account('240801', 'IVA Generado', 'CREDITO', 'PASIVO')
    ensure_account('236515', 'Retención Honorarios 10%', 'CREDITO', 'PASIVO')
    ensure_account('236540', 'Retención Compras 2.5%', 'CREDITO', 'PASIVO')
    
    # Income
    ensure_account('413505', 'Venta y Dist. Impresos', 'CREDITO', 'INGRESO')
    
    # Expenses
    ensure_account('510506', 'Sueldos', 'DEBITO', 'GASTO')
    ensure_account('513515', 'Servicios - Acueducto', 'DEBITO', 'GASTO')
    ensure_account('530505', 'Gastos Bancarios', 'DEBITO', 'GASTO')

def create_third_parties():
    print("\n>>> 2. Creating Third Parties...")
    
    # Clients
    ThirdParty.objects.get_or_create(
        identification_number='800111222',
        defaults={
            'party_type': 'CLIENTE',
            'person_type': 1,
            'business_name': 'CLIENTE EJEMPLO SAS',
            'identification_type': '31', # NIT
            'email': 'cliente@ejemplo.com',
            'phone': '3105556666',
            'address': 'Cra 100 # 11-22',
            'city_code': '76001', 'department_code': '76', 'country_code': 'CO', 'postal_code': '760033'
        }
    )
    
    ThirdParty.objects.get_or_create(
        identification_number='41234567',
        defaults={
            'party_type': 'CLIENTE',
            'person_type': 2,
            'first_name': 'JUAN',
            'surname': 'PEREZ',
            'identification_type': '13', # Cedula
            'email': 'juan.perez@email.com',
            'phone': '3120001111',
            'address': 'Av Principal 45',
            'city_code': '76001', 'department_code': '76', 'country_code': 'CO', 'postal_code': '760001'
        }
    )

    # Suppliers
    ThirdParty.objects.get_or_create(
        identification_number='900999888',
        defaults={
            'party_type': 'PROVEEDOR',
            'person_type': 1,
            'business_name': 'SUMINISTROS GLOBALES LTDA',
            'identification_type': '31',
            'email': 'ventas@suministros.co',
            'phone': '6015559999',
            'address': 'Zona Industrial Bodega 5',
            'city_code': '11001', 'department_code': '11', 'country_code': 'CO', 'postal_code': '110010'
        }
    )

    # Employees
    ThirdParty.objects.get_or_create(
        identification_number='88777666',
        defaults={
            'party_type': 'EMPLEADO',
            'person_type': 2,
            'first_name': 'MARIA',
            'surname': 'GONZALEZ',
            'identification_type': '13',
            'email': 'maria.g@satori.com',
            'phone': '3159998877',
            'address': 'Calle 5 # 4-3',
            'city_code': '76001', 'department_code': '76', 'country_code': 'CO', 'postal_code': '760001'
        }
    )

def create_document_types():
    print("\n>>> 3. Creating Document Types...")
    doc_types = [
        ('FV', 'Factura de Venta'),
        ('CE', 'Comprobante de Egreso'),
        ('RC', 'Recibo de Caja'),
        ('NC', 'Nota Crédito'),
        ('ND', 'Nota Débito'),
        ('CC', 'Cuenta de Cobro / Doc Soporte'),
        ('NI', 'Nota de Ingreso / Diario')
    ]
    for code, name in doc_types:
        AccountingDocumentType.objects.get_or_create(
            code=code, defaults={'name': name}
        )

def create_templates():
    print("\n>>> 4. Creating Accounting Templates...")
    
    # Template: Venta de Servicios (Factura)
    fv_type = AccountingDocumentType.objects.get(code='FV')
    template_fv, _ = AccountingTemplate.objects.get_or_create(
        name='VENTA SERVICIOS GENERAL + IVA',
        defaults={'document_type': fv_type}
    )
    
    if template_fv.lines.count() == 0:
        # 130505 - Clientes (Total)
        AccountingTemplateLine.objects.create(
            template=template_fv,
            account=Account.objects.get(code='130505'),
            nature='DEBITO',
            calculation_method='PLUG',
            description_template='Factura Venta {document_number}'
        )
        # 413505 - Ingresos (Subtotal)
        AccountingTemplateLine.objects.create(
            template=template_fv,
            account=Account.objects.get(code='413505'),
            nature='CREDITO',
            calculation_method='PERCENTAGE_OF_SUBTOTAL',
            value=100.00,
            description_template='Servicios Prestados'
        )
        # 240801 - IVA (19% of Subtotal)
        AccountingTemplateLine.objects.create(
            template=template_fv,
            account=Account.objects.get(code='240801'),
            nature='CREDITO',
            calculation_method='PERCENTAGE_OF_SUBTOTAL',
            value=19.00,
            description_template='IVA Generado 19%'
        )
        print("Created Template: VENTA SERVICIOS")

def create_dummy_movements():
    print("\n>>> 5. Creating Dummy Journal Entries (History)...")

    # Clean up potentially inconsistent previous runs
    JournalEntry.objects.filter(number__startswith='FV-1').delete()
    
    if JournalEntry.objects.count() > 5:
        print("Skipping entries, already populated.")
        return

    fv_type = AccountingDocumentType.objects.get(code='FV')
    client = ThirdParty.objects.get(identification_number='800111222')
    
    # Create 5 sales invoices
    for i in range(1, 6):
        net_value = Decimal(random.randint(1000, 5000)) * 1000
        iva = net_value * Decimal('0.19')
        total = net_value + iva
        
        entry = JournalEntry.objects.create(
            document_type=fv_type,
            number=f'FV-{1000+i}',
            date=datetime.now().date(),
            entry_type='VENTA',
            description=f'Venta de prueba #{i}',
            status='POSTED'
        )
        
        # Credit Income
        JournalEntryLine.objects.create(
            entry=entry,
            account=Account.objects.get(code='413505'),
            third_party=client,
            description='Servicios',
            debit=0,
            credit=net_value,
            line_number=1
        )
         # Credit IVA
        JournalEntryLine.objects.create(
            entry=entry,
            account=Account.objects.get(code='240801'),
            third_party=client,
            description='IVA 19%',
            debit=0,
            credit=iva,
            line_number=2
        )
         # Debit Client
        JournalEntryLine.objects.create(
            entry=entry,
            account=Account.objects.get(code='130505'),
            third_party=client,
            description=f'Factura FV-{1000+i}',
            debit=total,
            credit=0,
            line_number=3
        )
        print(f"Created Invoice {entry.number} for ${total:,.2f}")

if __name__ == '__main__':
    try:
        create_accounts()
        create_third_parties()
        create_document_types()
        create_templates()
        create_dummy_movements()
        print("\n✅ DATA LOAD COMPLETED SUCCESSFULLY!")
    except Exception as e:
        print(f"\n❌ ERROR LOADING DATA: {str(e)}")
        import traceback
        traceback.print_exc()
