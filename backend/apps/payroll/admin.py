from django.contrib import admin
from .models import LegalParameter, NoveltyType, EmployeeNovelty, Employee, PayrollPeriod, PayrollDocument, PayrollDetail

@admin.register(LegalParameter)
class LegalParameterAdmin(admin.ModelAdmin):
    list_display = ('get_key_display', 'value', 'valid_from', 'valid_to')
    list_filter = ('key',)
    search_fields = ('key',)

@admin.register(NoveltyType)
class NoveltyTypeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'dian_type', 'payroll_payment_percentage')
    list_filter = ('dian_type',)
    search_fields = ('code', 'name')

@admin.register(EmployeeNovelty)
class EmployeeNoveltyAdmin(admin.ModelAdmin):
    list_display = ('employee', 'novelty_type', 'start_date', 'days', 'total_value')
    list_filter = ('novelty_type', 'start_date')
    search_fields = ('employee__code', 'employee__third_party__name')

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('code', 'third_party', 'contract_type', 'is_active')
    search_fields = ('code',)

admin.site.register(PayrollPeriod)
admin.site.register(PayrollDocument)
admin.site.register(PayrollDetail)

from .models import PayrollConcept

@admin.register(PayrollConcept)
class PayrollConceptAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'concept_type', 'percentage', 'dian_code')
    list_filter = ('concept_type',)
    search_fields = ('code', 'name')
