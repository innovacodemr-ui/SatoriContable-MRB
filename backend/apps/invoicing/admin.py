from django.contrib import admin
from .models import DianResolution, SupportDocument, SupportDocumentDetail, ElectronicBillingConfig, DocumentSequence

class SupportDocumentDetailInline(admin.TabularInline):
    model = SupportDocumentDetail
    extra = 1

@admin.register(SupportDocument)
class SupportDocumentAdmin(admin.ModelAdmin):
    list_display = ('prefix', 'consecutive', 'supplier', 'issue_date', 'total', 'dian_status')
    inlines = [SupportDocumentDetailInline]
    list_filter = ('dian_status', 'issue_date')
    search_fields = ('supplier__name', 'consecutive')

@admin.register(DianResolution)
class DianResolutionAdmin(admin.ModelAdmin):
    list_display = ('client', 'resolution_number', 'prefix', 'number_from', 'number_to', 'current_number', 'date_to', 'is_active')
    list_filter = ('document_type', 'is_active', 'client')

@admin.register(ElectronicBillingConfig)
class ElectronicBillingConfigAdmin(admin.ModelAdmin):
    list_display = ('client', 'environment', 'software_id', 'created_at')
    list_filter = ('environment',)

@admin.register(DocumentSequence)
class DocumentSequenceAdmin(admin.ModelAdmin):
    list_display = ('client', 'document_type', 'prefix', 'current_number', 'is_active')
    list_filter = ('document_type', 'is_active', 'client')

