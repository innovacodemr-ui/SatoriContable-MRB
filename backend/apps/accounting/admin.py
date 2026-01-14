from django.contrib import admin
from .models import (
    AccountClass, AccountGroup, Account,
    CostCenter, ThirdParty, JournalEntry, JournalEntryLine
)


@admin.register(AccountClass)
class AccountClassAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'nature', 'is_active']
    list_filter = ['nature', 'is_active']
    search_fields = ['code', 'name']


@admin.register(AccountGroup)
class AccountGroupAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'account_class', 'is_active']
    list_filter = ['account_class', 'is_active']
    search_fields = ['code', 'name']


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'account_type', 'nature', 'level', 'allows_movement', 'is_active']
    list_filter = ['account_type', 'nature', 'level', 'allows_movement', 'is_active', 'is_tax_account']
    search_fields = ['code', 'name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = [
        ('Información Básica', {
            'fields': ['account_group', 'code', 'name', 'description', 'level']
        }),
        ('Clasificación', {
            'fields': ['parent', 'account_type', 'nature']
        }),
        ('Configuración', {
            'fields': [
                'allows_movement', 'requires_third_party',
                'requires_cost_center', 'manages_retention'
            ]
        }),
        ('Impuestos', {
            'fields': ['is_tax_account', 'tax_type'],
            'classes': ['collapse']
        }),
        ('Estado', {
            'fields': ['is_active', 'created_by', 'created_at', 'updated_at']
        }),
    ]


@admin.register(CostCenter)
class CostCenterAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'parent', 'is_active']
    list_filter = ['is_active']
    search_fields = ['code', 'name']


@admin.register(ThirdParty)
class ThirdPartyAdmin(admin.ModelAdmin):
    list_display = [
        'identification_number', 'get_full_name', 'party_type',
        'person_type', 'tax_regime', 'get_city_name', 'is_active'
    ]
    list_filter = ['party_type', 'person_type', 'tax_regime', 'is_active']
    search_fields = [
        'identification_number', 'first_name', 'surname', 'second_surname',
        'business_name', 'trade_name', 'email'
    ]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = [
        ('Tipo', {
            'fields': ['party_type', 'person_type']
        }),
        ('Identificación DIAN', {
            'fields': ['identification_type', 'identification_number', 'check_digit']
        }),
        ('Persona Jurídica', {
            'fields': ['business_name', 'trade_name'],
            'classes': ['collapse']
        }),
        ('Persona Natural', {
            'fields': ['first_name', 'middle_name', 'surname', 'second_surname'],
            'classes': ['collapse']
        }),
        ('Ubicación DANE', {
            'fields': [
                'country_code', 'department_code', 'city_code',
                'postal_code', 'address'
            ]
        }),
        ('Responsabilidades Fiscales', {
            'fields': ['tax_regime', 'fiscal_responsibilities', 'ciiu_code']
        }),
        ('Contacto', {
            'fields': ['email', 'phone', 'mobile']
        }),
        ('Información Bancaria', {
            'fields': ['bank_name', 'bank_account_type', 'bank_account_number'],
            'classes': ['collapse']
        }),
        ('Configuración Contable', {
            'fields': ['default_account']
        }),
        ('Estado', {
            'fields': ['is_active', 'notes', 'created_at', 'updated_at']
        }),
    ]
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Nombre Completo'
    
    def get_city_name(self, obj):
        return f"{obj.city_code}"
    get_city_name.short_description = 'Ciudad (DANE)'


class JournalEntryLineInline(admin.TabularInline):
    model = JournalEntryLine
    extra = 2
    fields = ['line_number', 'account', 'third_party', 'cost_center', 'description', 'debit', 'credit']
    autocomplete_fields = ['account', 'third_party', 'cost_center']


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ['number', 'entry_type', 'date', 'description', 'status', 'created_by']
    list_filter = ['entry_type', 'status', 'date']
    search_fields = ['number', 'description', 'reference']
    readonly_fields = ['created_at', 'updated_at', 'posted_at', 'posted_by']
    inlines = [JournalEntryLineInline]
    
    fieldsets = [
        ('Información Básica', {
            'fields': ['number', 'entry_type', 'date', 'description']
        }),
        ('Referencias', {
            'fields': ['reference', 'external_reference']
        }),
        ('Estado', {
            'fields': ['status', 'created_by', 'posted_by', 'posted_at']
        }),
        ('Notas', {
            'fields': ['notes', 'attachments'],
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]


@admin.register(JournalEntryLine)
class JournalEntryLineAdmin(admin.ModelAdmin):
    list_display = ['entry', 'line_number', 'account', 'third_party', 'debit', 'credit']
    list_filter = ['entry__date', 'entry__status']
    search_fields = ['entry__number', 'account__code', 'account__name', 'description']
    autocomplete_fields = ['entry', 'account', 'third_party', 'cost_center']
