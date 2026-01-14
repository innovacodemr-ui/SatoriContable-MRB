from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from apps.treasury.models import PaymentOut
from apps.accounting.models import JournalEntry, JournalEntryLine, Account
from apps.accounting.models import ThirdParty # Assuming we can find the third party by name or ID

class TreasuryService:
    @staticmethod
    @transaction.atomic
    def post_payment(payment_id):
        """
        Contabiliza un Comprobante de Egreso (PaymentOut).
        Genera el asiento contable: 
          DB: Cuentas por Pagar (Proveedores) 
          CR: Banco (Activo)
        """
        payment = PaymentOut.objects.get(pk=payment_id)
        
        if payment.status != 'DRAFT':
            raise ValueError("Solo se pueden contabilizar pagos en estado Borrador.")
            
        # 1. Crear Asiento Contable
        entry = JournalEntry.objects.create(
            client=payment.client,  # CRITICAL: Tenant Isolation
            entry_type='EGRESO', 
            number=f"CE-{payment.consecutive}",
            date=payment.payment_date,
            description=f"Pago a {payment.third_party} - {payment.notes}",
            content_type=ContentType.objects.get_for_model(payment),
            object_id=payment.pk,
            status='POSTED'
        )

        # 2. Líneas del Asiento
        
        # A. Crédito al Banco (Salida de dinero)
        bank_line = JournalEntryLine.objects.create(
            client=payment.client,
            entry=entry,
            line_number=1,
            account=payment.bank_account.gl_account,
            description=f"Pago CE-{payment.consecutive}",
            debit=Decimal('0'),
            credit=payment.total_amount
        )
        
        # B. Débito a Cuentas por Pagar (Disminución de pasivo)
        line_num = 2
        for detail in payment.details.all():
            # Buscar cuenta por pagar
            # 1. Intentar usar la cuenta por defecto del proveedor
            payable_account = payment.third_party.default_account
            
            # 2. Si no, buscar una cuenta 2205 (Nacionales) en el plan de cuentas del cliente
            if not payable_account:
                payable_account = Account.objects.filter(
                    client=payment.client, 
                    code__startswith='2205'
                ).first()
            
            if not payable_account:
                 raise ValueError(f"No se encontró una cuenta contable para imputar el pago al proveedor {payment.third_party}.")

            JournalEntryLine.objects.create(
                client=payment.client,
                entry=entry,
                line_number=line_num,
                account=payable_account,
                third_party=payment.third_party, # Vinculación real
                description=f"Pago Factura {detail.invoice.invoice_number}",
                debit=detail.amount_paid,
                credit=Decimal('0')
            )
            line_num += 1

        # 3. Actualizar estado del Pago
        payment.status = 'POSTED'
        payment.save()
        
        return entry
