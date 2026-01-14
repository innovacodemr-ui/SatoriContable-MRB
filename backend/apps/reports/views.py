from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Q
import datetime
from decimal import Decimal

from apps.invoicing.models import Invoice
from apps.accounting.models import JournalEntryLine
from apps.treasury.models import BankAccount

class DashboardMetricsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = datetime.date.today()
        # Primer día del mes actual
        first_day = today.replace(day=1)
        
        # 1. Ventas del Mes (Facturas POSTED)
        # Usamos Total (incluye IVA) o Subtotal? El usuario pidió "Ventas", generalmente es Ingreso Neto (Subtotal),
        # pero para "Flujo" suele pensarse en Total.
        # El ejemplo del usuario "$1.190.000" coincide con el Total de la factura de prueba.
        # Usaremos Invoice.total.
        sales_data = Invoice.objects.filter(
            status='POSTED',
            issue_date__gte=first_day,
            issue_date__lte=today
        ).aggregate(total_sales=Sum('total'))
        
        sales_month = sales_data['total_sales'] or 0

        # 2. Gastos del Mes (Clase 5 y 6)
        # Consultamos el motor contable directamente
        # Gastos = Débitos - Créditos en cuentas 5xxx y 6xxx
        expense_lines = JournalEntryLine.objects.filter(
            (Q(account__code__startswith='5') | Q(account__code__startswith='6')),
            entry__date__gte=first_day,
            entry__date__lte=today,
            entry__status='POSTED' # Solo asientos confirmados
        )
        
        exp_debits = expense_lines.aggregate(t=Sum('debit'))['t'] or 0
        exp_credits = expense_lines.aggregate(t=Sum('credit'))['t'] or 0
        expenses_month = exp_debits - exp_credits

        # 3. Disponible en Bancos (Real Time)
        # Saldo de las cuentas PUC asociadas a Tesorería
        # Activo (1xxx) aumenta por Débito, disminuye por Crédito
        bank_accounts = BankAccount.objects.all()
        # Si no hay cuentas bancarias configuradas, buscamos genéricamente en la 1110 (Bancos) y 1105 (Caja)
        if bank_accounts.exists():
            bank_gl_ids = bank_accounts.values_list('gl_account_id', flat=True)
            bank_lines = JournalEntryLine.objects.filter(
                account_id__in=bank_gl_ids,
                entry__status='POSTED'
            )
        else:
            # Fallback: Cuentas 11 (Disponible)
            bank_lines = JournalEntryLine.objects.filter(
                account__code__startswith='11',
                entry__status='POSTED'
            )
            
        bank_debits = bank_lines.aggregate(t=Sum('debit'))['t'] or 0
        bank_credits = bank_lines.aggregate(t=Sum('credit'))['t'] or 0
        available_cash = bank_debits - bank_credits

        return Response({
            'period': f"{first_day.strftime('%B %Y')}",
            'sales_month': sales_month,
            'expenses_month': expenses_month,
            'available_cash': available_cash,
            'chart_data': [
                {'name': 'Ventas', 'value': sales_month, 'fill': '#4caf50'},
                {'name': 'Gastos', 'value': expenses_month, 'fill': '#f44336'},
            ]
        })
