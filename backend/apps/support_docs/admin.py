from django.contrib import admin
from .models import DianResolution, SupportDocument, SupportDocumentDetail, Supplier

class SupportDocumentDetailInline(admin.TabularInline):
    model = SupportDocumentDetail
    extra = 1

@admin.register(SupportDocument)
class SupportDocumentAdmin(admin.ModelAdmin):
    list_display = ('resolution', 'consecutive', 'supplier', 'issue_date', 'total', 'dian_status')
    inlines = [SupportDocumentDetailInline]
    list_filter = ('dian_status', 'issue_date')
    search_fields = ('supplier__business_name', 'supplier__first_name', 'supplier__identification_number', 'consecutive')

@admin.register(DianResolution)
class DianResolutionAdmin(admin.ModelAdmin):
    list_display = ('resolution_number', 'prefix', 'from_number', 'to_number', 'current_number', 'end_date', 'is_active')
    list_filter = ('is_active',)

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('identification_number', 'get_full_name', 'email')
    search_fields = ('business_name', 'first_name', 'surname', 'identification_number')
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Nombre'
