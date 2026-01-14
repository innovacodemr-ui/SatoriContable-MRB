from celery import shared_task
from apps.tenants.models import Client
from cryptography import x509
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.backends import default_backend
from datetime import datetime, timedelta

@shared_task
def check_certificate_expiration():
    for client in Client.objects.all():
        if client.dian_certificate:
            try:
                pfx_data = client.dian_certificate.read()
                password = client.certificate_password_encrypted.encode('utf-8') # This should be decrypted
                private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(
                    pfx_data,
                    password,
                    default_backend()
                )
                if certificate:
                    expiration_date = certificate.not_valid_after
                    if expiration_date - timedelta(days=30) < datetime.now():
                        # Create a notification for the client
                        # This is a placeholder for the actual implementation
                        print(f"Certificate for {client.name} is about to expire on {expiration_date}")
            except Exception as e:
                print(f"Error checking certificate for {client.name}: {e}")
