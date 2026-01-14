import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.electronic_events.services.email_service import EmailReceptionService

try:
    print("Iniciando prueba manual...")
    service = EmailReceptionService()
    result = service.fetch_invoices()
    print(json.dumps(result, indent=2))
except Exception as e:
    print(f"Error critico: {e}")
