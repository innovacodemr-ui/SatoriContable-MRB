from django.contrib import admin
from .models import (
    ElectronicDocument, ElectronicDocumentLine,
    DIANResolution, DIANLog, TaxType, ElectronicDocumentTax
)


class ElectronicDocumentLineInline(admin.TabularInline):
    model = ElectronicDocumentLine
    extra = 1
    fields = [
        'line_number', 'product_code', 'product_name',
        'quantity', 'unit_price', 'discount_amount',
        'tax_rate', 'tax_amount', 'total'
    ]


class ElectronicDocumentTaxInline(admin.TabularInline):
    model = ElectronicDocumentTax
    extra = 0
    fields = ['tax_type', 'taxable_amount', 'tax_rate', 'tax_amount']


@admin.register(ElectronicDocument)
class ElectronicDocumentAdmin(admin.ModelAdmin):
    list_display = [
        'full_number', 'document_type', 'customer',
        'issue_date', 'total', 'status', 'cufe'
    ]
    list_filter = ['document_type', 'status', 'issue_date', 'payment_method']
    search_fields = ['full_number', 'number', 'cufe', 'customer__business_name']
    readonly_fields = [
        'full_number', 'cufe', 'qr_code',
        'created_at', 'updated_at',
        'dian_sent_at', 'dian_accepted_at'
    ]
    inlines = [ElectronicDocumentLineInline, ElectronicDocumentTaxInline]
    
    fieldsets = [
        ('Información Básica', {
            'fields': ['document_type', 'prefix', 'number', 'full_number', 'customer']
        }),
        ('Fechas', {
            'fields': ['issue_date', 'due_date']
        }),
        ('DIAN', {
            'fields': ['cufe', 'qr_code', 'status', 'dian_response', 'dian_sent_at', 'dian_accepted_at']
        }),
        ('Moneda y Totales', {
            'fields': ['currency', 'exchange_rate', 'subtotal', 'tax_total', 'discount_total', 'total']
        }),
        ('Pago', {
            'fields': ['payment_method', 'payment_terms']
        }),
        ('Archivos', {
            'fields': ['xml_file', 'pdf_file', 'attached_document'],
            'classes': ['collapse']
        }),
        ('Notas', {
            'fields': ['notes', 'internal_notes'],
            'classes': ['collapse']
        }),
        ('Metadata', {
            'fields': ['created_by', 'created_at', 'updated_at', 'metadata'],
            'classes': ['collapse']
        }),
    ]


@admin.register(ElectronicDocumentLine)
class ElectronicDocumentLineAdmin(admin.ModelAdmin):
    list_display = [
        'document', 'line_number', 'product_name',
        'quantity', 'unit_price', 'total'
    ]
    list_filter = ['document__issue_date']
    search_fields = ['document__full_number', 'product_code', 'product_name']


@admin.register(DIANResolution)
class DIANResolutionAdmin(admin.ModelAdmin):
    list_display = [
        'resolution_number', 'prefix', 'start_number',
        'end_number', 'current_number', 'valid_from',
        'valid_to', 'is_active', 'is_test'
    ]
    list_filter = ['is_active', 'is_test', 'valid_from', 'valid_to']
    search_fields = ['resolution_number', 'prefix']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = [
        ('Información de la Resolución', {
            'fields': ['resolution_number', 'resolution_date']
        }),
        ('Numeración', {
            'fields': ['prefix', 'start_number', 'end_number', 'current_number']
        }),
        ('Vigencia', {
            'fields': ['valid_from', 'valid_to']
        }),
        ('Configuración Técnica', {
            'fields': ['technical_key', 'test_set_id']
        }),
        ('Estado', {
            'fields': ['is_active', 'is_test', 'notes']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]


@admin.register(DIANLog)
class DIANLogAdmin(admin.ModelAdmin):
    list_display = ['document', 'action', 'status', 'created_at', 'user']
    list_filter = ['action', 'status', 'created_at']
    search_fields = ['document__full_number', 'message', 'error_message']
    readonly_fields = ['created_at']
    
    fieldsets = [
        ('Información', {
            'fields': ['document', 'action', 'status', 'user']
        }),
        ('Request y Response', {
            'fields': ['request_data', 'response_data']
        }),
        ('Mensajes', {
            'fields': ['message', 'error_message']
        }),
        ('Timestamp', {
            'fields': ['created_at']
        }),
    ]


@admin.register(TaxType)
class TaxTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'category', 'default_rate', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['code', 'name']


@admin.register(ElectronicDocumentTax)
class ElectronicDocumentTaxAdmin(admin.ModelAdmin):
    list_display = ['document', 'tax_type', 'taxable_amount', 'tax_rate', 'tax_amount']
    list_filter = ['tax_type', 'document__issue_date']
    search_fields = ['document__full_number']
