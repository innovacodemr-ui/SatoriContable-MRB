from django.contrib import admin
from .models import BankAccount, PaymentOut

@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ('client', 'name', 'bank_name', 'account_number', 'currency')
    list_filter = ('client', 'bank_name')
    search_fields = ('name', 'account_number')

@admin.register(PaymentOut)
class PaymentOutAdmin(admin.ModelAdmin):
    list_display = ('client', 'consecutive', 'payment_date', 'third_party', 'total_amount', 'status')
    list_filter = ('client', 'status', 'payment_date')
    search_fields = ('consecutive', 'third_party__business_name', 'third_party__first_name')
