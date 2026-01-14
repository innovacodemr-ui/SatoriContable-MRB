from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _
from apps.accounting.models import Account
from apps.electronic_events.models import ReceivedInvoice

class BankAccount(models.Model):
    client = models.ForeignKey('tenants.Client', on_delete=models.CASCADE, verbose_name="Cliente (Tenant)", null=True, blank=True)
    name = models.CharField(max_length=100, verbose_name="Nombre")
    account_number = models.CharField(max_length=50, verbose_name="Número de Cuenta")
    bank_name = models.CharField(max_length=100, verbose_name="Banco")
    currency = models.CharField(max_length=3, default='COP', verbose_name="Moneda")
    gl_account = models.ForeignKey(Account, on_delete=models.PROTECT, verbose_name="Cuenta Contable (PUC)")

    def __str__(self):
        return f"{self.bank_name} - {self.name} ({self.currency})"
    
    class Meta:
        verbose_name = "Cuenta Bancaria"
        verbose_name_plural = "Cuentas Bancarias"
        unique_together = ('client', 'account_number')

class PaymentOut(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Borrador'),
        ('POSTED', 'Contabilizado'),
        ('CANCELLED', 'Anulado'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('TRANSFERENCIA', 'Transferencia Bancaria'),
        ('CHEQUE', 'Cheque'),
        ('EFECTIVO', 'Efectivo'),
    ]

    client = models.ForeignKey('tenants.Client', on_delete=models.CASCADE, verbose_name="Cliente (Tenant)", null=True, blank=True)
    consecutive = models.IntegerField(verbose_name="Consecutivo", editable=False)
    payment_date = models.DateField(verbose_name="Fecha de Pago")
    third_party = models.ForeignKey('accounting.ThirdParty', on_delete=models.PROTECT, verbose_name="Tercero (Proveedor)", null=True, blank=True)
    bank_account = models.ForeignKey(BankAccount, on_delete=models.PROTECT, verbose_name="Cuenta Bancaria")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='TRANSFERENCIA', verbose_name="Método de Pago")
    total_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0, verbose_name="Monto Total")
    notes = models.TextField(blank=True, verbose_name="Observaciones")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT', verbose_name="Estado")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.consecutive:
            # Consecutivo por Cliente
            last = PaymentOut.objects.filter(client=self.client).order_by('-consecutive').first()
            if last:
                self.consecutive = last.consecutive + 1
            else:
                self.consecutive = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"CE-{self.consecutive} {self.third_party}"

    class Meta:
        verbose_name = "Comprobante de Egreso"
        verbose_name_plural = "Comprobantes de Egreso"
        unique_together = ('client', 'consecutive')


class PaymentOutDetail(models.Model):
    payment_out = models.ForeignKey(PaymentOut, related_name='details', on_delete=models.CASCADE, verbose_name="Comprobante de Egreso")
    invoice = models.ForeignKey(ReceivedInvoice, related_name='payments', on_delete=models.PROTECT, verbose_name="Factura de Proveedor")
    amount_paid = models.DecimalField(max_digits=18, decimal_places=2, verbose_name="Monto Pagado")

    def clean(self):
        # Evitar pagar más del saldo
        # Saldo = Total Factura - Pagos PREVIOS (excluyendo este si se está editando)
        # Consideramos pagos en estado POSTED o DRAFT? 
        # Para ser conservadores, todos los pagos activos (no CANCELLED) restan cupo.
        
        existing_payments = PaymentOutDetail.objects.filter(
            invoice=self.invoice
        ).exclude(payment_out__status='CANCELLED')
        
        if self.pk:
            existing_payments = existing_payments.exclude(pk=self.pk)
            
        total_paid_already = existing_payments.aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
        
        balance = self.invoice.total_amount - total_paid_already
        
        if self.amount_paid > balance:
            raise ValidationError(
                f"El monto a pagar ({'{:,.2f}'.format(self.amount_paid)}) excede el saldo pendiente de la factura ({'{:,.2f}'.format(balance)})."
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
        
    class Meta:
        verbose_name = "Detalle de Pago"
        verbose_name_plural = "Detalles de Pago"
