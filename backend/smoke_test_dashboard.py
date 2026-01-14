import os
import django
import sys
from decimal import Decimal

sys.path.append(os.path.join(os.getcwd(), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.accounting.models import Account, JournalEntry, JournalEntryLine, AccountingDocumentType
from rest_framework.test import APIRequestFactory, force_authenticate
from apps.reports.views import DashboardMetricsView
from django.contrib.auth import get_user_model

def verify_dashboard():
    print("--- OPERACIÓN BARRA ROJA (Simulación de Gasto) ---")
    
    User = get_user_model()
    user = User.objects.filter(is_superuser=True).first()
    if not user:
        print("❌ No admin user found. Creating one...")
        user = User.objects.create_superuser('test_admin', 'admin@test.com', 'admin123')

    # 0. Helper to get Dash Stats
    def get_stats(label):
        factory = APIRequestFactory()
        request = factory.get('/api/reports/dashboard/')
        force_authenticate(request, user=user)
        view = DashboardMetricsView.as_view()
        response = view(request)
        data = response.data
        print(f"\n📊 [{label}] Estado del Tablero:")
        print(f"   💰 Ventas Mes: ${data['sales_month']:,.0f}")
        print(f"   📉 Gastos Mes: ${data['expenses_month']:,.0f}")
        print(f"   🏦 Bancos:     ${data['available_cash']:,.0f}")
        return data

    # 1. State Before
    get_stats("ANTES")

    # 2. Execute Expense (Manual Entry)
    print("\n--- EJECUTANDO GASTO MANUAL ---")
    
    # Check Accounts
    # 5135 - Servicios
    # 1110 - Bancos
    
    try:
        # We search with startswith because I don't know the exact full code in the DB
        acc_expense = Account.objects.filter(code__startswith='5135').first()
        acc_bank = Account.objects.filter(code__startswith='1110').first()
        
        if not acc_expense:
             # Create dummy if not exists just for the test (or fallback to any 5)
             acc_expense = Account.objects.filter(code__startswith='5').first()
             if not acc_expense:
                 print("❌ No hay cuentas de Gastos (5xxx) en el sistema.")
                 return
        
        if not acc_bank:
             acc_bank = Account.objects.filter(code__startswith='11').first()
             if not acc_bank:
                 print("❌ No hay cuentas de Activo (11xx) en el sistema.")
                 return

        print(f"   Usando Cuenta Gasto: {acc_expense.code} - {acc_expense.name}")
        print(f"   Usando Cuenta Banco: {acc_bank.code} - {acc_bank.name}")

        # Document Type (Comprobante de Egreso typically, but we use Diario for manual)
        doc_type, _ = AccountingDocumentType.objects.get_or_create(
            code='CD',
            defaults={'name': 'Comprobante de Diario', 'current_number': 0}
        )
        doc_type.current_number += 1
        doc_type.save()

        # Create Entry
        entry = JournalEntry.objects.create(
            document_type=doc_type,
            number=f"CD-{doc_type.current_number}",
            date=user.date_joined.date().today(), # Today
            entry_type='DIARIO',
            description="Pago Servicios Públicos Prueba (Simulación)",
            status='POSTED'
        )

        # Lines
        amount = Decimal('200000.00')

        # Debit Expense
        JournalEntryLine.objects.create(
            entry=entry,
            line_number=1,
            account=acc_expense,
            description="Pago Servicios",
            debit=amount,
            credit=0
        )
        
        # Credit Bank
        JournalEntryLine.objects.create(
            entry=entry,
            line_number=2,
            account=acc_bank,
            description="Salida Banco",
            debit=0,
            credit=amount
        )
        
        print(f"✅ Asiento Contable Creado: {entry.number} - Valor: ${amount:,.0f}")

    except Exception as e:
        print(f"❌ Error creando gasto: {e}")
        return

    # 3. State After
    data_after = get_stats("DESPUÉS")

    # 4. Validation
    if data_after['expenses_month'] > 0:
        print("\n🎉 VICTORIA: ¡La Barra Roja ha aparecido!")
        print("   Satori ha detectado el movimiento contable en los reportes.")
    else:
        print("\n⚠️ ALERTA: El gasto no se reflejó en el Dashboard.")

if __name__ == '__main__':
    verify_dashboard()
