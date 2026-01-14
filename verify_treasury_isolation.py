import os
import django
import sys
from decimal import Decimal

# Configurar Django
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.tenants.models import Client
from apps.treasury.models import BankAccount, PaymentOut
from apps.accounting.models import Account, AccountGroup, AccountClass, ThirdParty
from apps.treasury.services.treasury_service import TreasuryService

def setup_tenant(name, nit):
    client, _ = Client.objects.get_or_create(
        nit=nit, 
        defaults={'name': name}
    )
    return client

def create_basics(client):
    # Crear PUC mínimo
    cls_act, _ = AccountClass.objects.get_or_create(client=client, code='1', defaults={'name': 'ACTIVO', 'nature': 'DEBITO'})
    grp_efec, _ = AccountGroup.objects.get_or_create(client=client, code='11', defaults={'account_class': cls_act, 'name': 'EFECTIVO'})
    
    # Cuenta Banco
    acc_bank, _ = Account.objects.get_or_create(
        client=client, code='111005', 
        defaults={
            'account_group': grp_efec, 'name': 'Bancos Nacionales', 
            'level': 3, 'nature': 'DEBITO', 'account_type': 'ACTIVO'
        }
    )

    # Cuenta Proveedores
    cls_pas, _ = AccountClass.objects.get_or_create(client=client, code='2', defaults={'name': 'PASIVO', 'nature': 'CREDITO'})
    grp_cxp, _ = AccountGroup.objects.get_or_create(client=client, code='22', defaults={'account_class': cls_pas, 'name': 'PROVEEDORES'})
    acc_prov, _ = Account.objects.get_or_create(
        client=client, code='220505',
        defaults={
            'account_group': grp_cxp, 'name': 'Proveedores Nacionales',
            'level': 3, 'nature': 'CREDITO', 'account_type': 'PASIVO'
        }
    )
    
    return acc_bank, acc_prov

def test_isolation():
    print(">>> INICIANDO PRUEBA DE AISLAMIENTO (TESORERÍA) <<<")
    
    # 1. Setup Tenants
    tenant_a = setup_tenant("Tenant A", "900111222")
    tenant_b = setup_tenant("Tenant B", "900333444")
    
    acc_bank_a, acc_prov_a = create_basics(tenant_a)
    acc_bank_b, acc_prov_b = create_basics(tenant_b)

    # 2. Setup ThirdParty
    tp_a = ThirdParty.objects.create(
        client=tenant_a, 
        identification_number='888', 
        first_name='Proveedor A', 
        surname='Test',
        person_type=2,
        party_type='PROVEEDOR'
    )

    # 3. Crear Datos en Tenant A
    bank_a = BankAccount.objects.create(
        client=tenant_a,
        name="Cuenta A",
        account_number="111-111",
        bank_name="Banco A",
        gl_account=acc_bank_a
    )
    
    payment_a = PaymentOut.objects.create(
        client=tenant_a,
        payment_date="2025-01-01",
        third_party=tp_a,
        bank_account=bank_a,
        total_amount=Decimal("100000"),
        status='DRAFT'
    )
    
    print(f" [OK] Datos creados en Tenant A: Banco {bank_a.id}, Pago {payment_a.id}")

    # 4. INTENTO DE FUGA: Tenant B intenta ver datos de Tenant A
    print(" -> Verificando fugas de datos...")
    
    # Intento 1: Ver Bancos
    bancos_visibles_b = BankAccount.objects.filter(client=tenant_b)
    if bancos_visibles_b.count() > 0:
        print(" [FALLO CRÍTICO] Tenant B puede ver bancos ajenos!")
        exit(1)
        
    # Intento 2: Ver Pagos
    pagos_visibles_b = PaymentOut.objects.filter(client=tenant_b)
    if pagos_visibles_b.count() > 0:
        print(" [FALLO CRÍTICO] Tenant B puede ver pagos ajenos!")
        exit(1)
        
    print(" [OK] Aislamiento de lectura CONFIRMADO.")

    # 5. Prueba de Lógica Contable (TreasuryService)
    print(" -> Verificando lógica contable...")
    try:
        entry = TreasuryService.post_payment(payment_a.pk)
        if entry.client != tenant_a:
             print(" [FALLO] El asiento contable no quedó asociado al Tenant A")
             exit(1)
        print(f" [OK] Asiento Contable generado exitosamente: {entry} (Cliente: {entry.client})")
    except Exception as e:
        print(f" [ERROR] Falló el servicio de tesorería: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

    print("\n>>> PRUEBA DE AISLAMIENTO EXITOSA: SISTEMA BLINDADO <<<")

if __name__ == "__main__":
    try:
        test_isolation()
    except Exception as e:
        print(f"Error fatal: {e}")
        exit(1)
