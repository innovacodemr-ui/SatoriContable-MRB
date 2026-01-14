import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.accounting.models import Account, AccountClass, AccountGroup, ThirdParty
from apps.electronic_events.models import ReceivedInvoice

def prepare_data():
    print("--- Verificando Prerrequisitos para Drill Test ---\n")
    
    # 1. Verificar Cuenta de Bancos 111005
    try:
        # Hierarchy: Class -> Group -> Account
        # Class 1: ACTIVO
        acc_class, _ = AccountClass.objects.get_or_create(
            code='1', defaults={'name': 'ACTIVO', 'nature': 'DEBITO'}
        )
        # Group 11: DISPONIBLE
        acc_group, _ = AccountGroup.objects.get_or_create(
            code='11', defaults={
                'name': 'DISPONIBLE', 
                'account_class': acc_class,
                # 'nature': 'DEBITO'  <-- Error: AccountGroup does not have 'nature'
            }
        )
        
        account_code = '111005'
        account, created = Account.objects.get_or_create(
            code=account_code,
            defaults={
                'name': 'Bancolombia Moneda Nacional',
                'account_group': acc_group,
                'nature': 'DEBITO',
                'account_type': 'ACTIVO',
                'level': 6,
                'is_active': True,
                'allows_movement': True
            }
        )
        
        if created:
            print(f"✅ Cuenta {account_code} creada.")
        else:
            print(f"✅ Cuenta {account_code} verificada.")

        # Ensure Supplier Account 2205 (for testing post logic fallback)
        acc_class_2, _ = AccountClass.objects.get_or_create(
            code='2', defaults={'name': 'PASIVO', 'nature': 'CREDITO'}
        )
        acc_group_22, _ = AccountGroup.objects.get_or_create(
            code='22', defaults={'name': 'PROVEEDORES', 'account_class': acc_class_2} # No nature
        )
        Account.objects.get_or_create(code='220505', defaults={
             'name': 'Proveedores Nacionales',
             'account_group': acc_group_22,
             'nature': 'CREDITO',
             'account_type': 'PASIVO',
             'level': 6,
             'allows_movement': True
        })
        print(f"✅ Cuenta 220505 verificada.")
            
    except Exception as e:
        print(f"❌ Error verificando cuentas: {e}")

    # 2. Verificar Proveedor de Prueba
    try:
        supplier_nit = '900123456'
        supplier, created = ThirdParty.objects.get_or_create(
            identification_number=supplier_nit,
            defaults={
                'party_type': 'PROVEEDOR',
                'person_type': 1,
                'business_name': 'PROVEEDOR DE PRUEBA SAS', # Correct field name
                'identification_type': '31', # NIT
                'email': 'proveedor@test.com',
                'address': 'Calle Falsa 123',
                # Correct field names for location
                'city_code': '76001', 
                'department_code': '76',
                'postal_code': '760001',
                'phone': '3001234567',
                'tax_regime': '48', # Responsable de IVA
                'country_code': 'CO'
            }
        )
        if created:
            print(f"✅ Proveedor de Prueba creado.")
        else:
            print(f"✅ Proveedor de Prueba verificado.")
            
    except Exception as e:
        print(f"❌ Error verificando proveedor: {e}")

    print("\n--- Prerrequisitos listos. Puede proceder al Frontend. ---")

if __name__ == '__main__':
    prepare_data()
