import sys
import os
import django

sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.tenants.models import Client

c = Client.objects.first()
if c:
    print(f"Client: {c.name}")
    print(f"SoftwareID: {c.dian_software_id}")
    print(f"Nit: {c.nit}")
    print(f"Cert P12: {c.dian_certificate}")
else:
    print("No Client found in DB.")
