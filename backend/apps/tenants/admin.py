from django.contrib import admin
# from django_tenants.admin import TenantAdminMixin
# from .models import Client #, Domain


# @admin.register(Client)
# class ClientAdmin(admin.ModelAdmin):
#     list_display = ['name', 'nit', 'tax_regime', 'city'] # , 'plan', 'is_active', 'created_on']
#     list_filter = ['tax_regime', 'city'] #, 'plan', 'is_active', 'city']
#     search_fields = ['name', 'nit', 'legal_name', 'email']
#     readonly_fields = ['created_on', 'modified_on', 'last_sync']
#     
#     fieldsets = [
#         ('Información Básica', {
#             'fields': ['name', 'nit', 'legal_name', 'business_name']
#         }),
#         ('Información Tributaria', {
#             'fields': ['tax_regime', 'fiscal_responsibilities']
#         }),
#         ('Ubicación', {
#             'fields': ['address', 'city', 'department', 'country', 'postal_code']
#         }),
#         ('Contacto', {
#             'fields': ['phone', 'email', 'website']
#         }),
#         ('Configuración DIAN', {
#             'fields': ['dian_software_id', 'dian_test_set_id', 'dian_certificate', 'dian_certificate_password']
#         }),
#         ('Plan y Estado', {
#             'fields': ['plan', 'is_active']
#         }),
#         ('Sincronización', {
#             'fields': ['sync_enabled', 'last_sync']
#         }),
#         ('Metadatos', {
#             'fields': ['metadata', 'created_on', 'modified_on'],
#             'classes': ['collapse']
#         }),
#     ]


# @admin.register(Domain)
# class DomainAdmin(admin.ModelAdmin):
#     list_display = ['domain', 'tenant', 'is_primary']
#     list_filter = ['is_primary']
#     search_fields = ['domain', 'tenant__name']
