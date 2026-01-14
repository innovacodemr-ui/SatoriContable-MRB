"""
Celery configuration for Satori Accounting System.
"""
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('satori')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat Schedule for periodic tasks
app.conf.beat_schedule = {
    # Sincronización de datos cada 5 minutos
    'sync-desktop-data': {
        'task': 'apps.sync.tasks.sync_desktop_data',
        'schedule': crontab(minute='*/5'),
    },
    # Generación de reportes diarios
    'generate-daily-reports': {
        'task': 'apps.reports.tasks.generate_daily_reports',
        'schedule': crontab(hour=23, minute=0),
    },
    # Verificación de documentos DIAN pendientes
    'check-dian-documents': {
        'task': 'apps.dian.tasks.check_pending_documents',
        'schedule': crontab(minute='*/15'),
    },
    # Auto-Sync: Recepción de Facturas por Correo
    'check-new-invoices-email': {
        'task': 'apps.electronic_events.tasks.check_new_dian_emails',
        'schedule': crontab(minute='*/5'),
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
