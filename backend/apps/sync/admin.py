from django.contrib import admin
from .models import SyncLog


@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    list_display = [
        'client_id', 'sync_type', 'status',
        'records_sent', 'records_received', 'records_failed',
        'created_at'
    ]
    list_filter = ['status', 'sync_type', 'created_at']
    search_fields = ['client_id']
    readonly_fields = ['created_at', 'started_at', 'completed_at']
    
    fieldsets = [
        ('Información', {
            'fields': ['client_id', 'sync_type', 'status', 'user']
        }),
        ('Estadísticas', {
            'fields': ['records_sent', 'records_received', 'records_failed']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'started_at', 'completed_at']
        }),
        ('Detalles', {
            'fields': ['error_message', 'sync_data'],
            'classes': ['collapse']
        }),
    ]
