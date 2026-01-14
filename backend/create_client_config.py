import os
import sys
import django
from django.core.files import File

# Setup Django Environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.tenants.models import Client
from apps.common.utils import SecurityService

def run():
    print("--- Configuring Client for DIAN Transmission ---")
    
    # 1. Check / Create Client
    client = Client.objects.first()
    if not client:
        print("Creating new Client...")
        client = Client(name="Empresa de Prueba S.A.S.", nit="900000000")
    else:
        print(f"Updating existing Client: {client.name}")

    # 2. Config Data
    client.legal_name = "Empresa de Prueba S.A.S."
    client.business_name = "Satori Demo"
    
    # Dummy UUIDs for initial connection attempts
    # In a real scenario, these must be provided by the user from their DIAN portal
    client.dian_software_id = "c3ecc883-9b19-4876-b371-33104e76d912"
    client.dian_test_set_id = "88a65522-68c4-4c4c-8822-192568603417"
    
    # 3. Certificate
    # Try multiple locations
    cert_paths = [
        'apps/dian/certs/certificate.p12', 
        'backend/apps/dian/certs/certificate.p12'
    ]
    
    cert_found = False
    for cert_path in cert_paths:
        if os.path.exists(cert_path):
            print(f"Found certificate at {cert_path}")
            with open(cert_path, 'rb') as f:
                # Django FileField saves to MEDIA_ROOT/dian_certificates/
                client.dian_certificate.save('certificate.p12', File(f), save=False)
                print("Certificate attached.")
            cert_found = True
            break
            
    if not cert_found:
        print(f"WARNING: Certificate NOT found in search paths: {cert_paths}")
        # Assuming if it returns 21 bytes check locally, etc, but we rely on what we saw.

    # 4. Password
    # Using the project default password discovered in verify_integration.py
    raw_password = 'Satori2026'
    client.certificate_password_encrypted = SecurityService.encrypt_password(raw_password)
    client.dian_certificate_password = raw_password # Legacy fallback
    
    client.save()
    print("Client configuration saved successfully.")
    print(f"Client ID: {client.id}")
    print(f"Certificate URL: {client.dian_certificate.name}")

if __name__ == '__main__':
    run()
