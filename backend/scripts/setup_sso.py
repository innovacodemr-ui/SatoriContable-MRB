import os
import sys
# Django setup is handled by manage.py shell
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from apps.tenants.models import Client
from apps.core.models import ClientDomain
from allauth.socialaccount.models import SocialApp
from apps.tenants.models import Client
from apps.core.models import ClientDomain

def setup():
    print(">>> Iniciando Configuración SSO Satori...")

    # 1. Configurar Site
    site, created = Site.objects.update_or_create(
        id=1,
        defaults={
            'domain': 'innovacode-mrb.com',
            'name': 'Satori MRB'
        }
    )
    print(f"✅ Site configurado: {site.domain}")

    # 2. Configurar SocialApps (Google & Microsoft)
    # Nota: Usamos placeholders si no hay env vars, el usuario debe editar en Admin.
    providers = [
        ('google', 'Google', os.getenv('GOOGLE_CLIENT_ID', 'CHANGE_ME_IN_ADMIN'), os.getenv('GOOGLE_SECRET', 'CHANGE_ME_IN_ADMIN')),
        ('microsoft', 'Microsoft', os.getenv('MICROSOFT_CLIENT_ID', 'CHANGE_ME_IN_ADMIN'), os.getenv('MICROSOFT_SECRET', 'CHANGE_ME_IN_ADMIN')),
    ]

    for provider_id, name, client_id, secret in providers:
        app, created = SocialApp.objects.update_or_create(
            provider=provider_id,
            defaults={
                'name': name,
                'client_id': client_id,
                'secret': secret,
                # 'key': '' # Not used for Google/MS usually
            }
        )
        app.sites.add(site)
        print(f"✅ SocialApp configurada: {name} (ID: {client_id[:5]}...)")

    # 3. Crear Tenant 'AB 11 S.A.S.'
    client, created = Client.objects.get_or_create(
        nit='900000000-1', # Dummy NIT, user should update if specific needed
        defaults={
            'name': 'AB 11 S.A.S.',
            'legal_name': 'AB 11 S.A.S.',
            'email': 'admin@ab11.com.co',
            'phone': '3000000000',
            'address': 'Calle Falsa 123',
            'city': 'Cali',
            'tax_regime': 'COMUN'
        }
    )
    if not created and client.name != 'AB 11 S.A.S.':
        client.name = 'AB 11 S.A.S.'
        client.save()
    print(f"✅ Tenant configurado: {client.name}")

    # 4. Vincular Dominio 'ab11.com.co'
    domain, created = ClientDomain.objects.get_or_create(
        domain='ab11.com.co',
        defaults={
            'client': client
        }
    )
    if not created and domain.client != client:
        domain.client = client
        domain.save()
    print(f"✅ Dominio vinculado: {domain.domain} -> {domain.client.name}")

    print(">>> Configuración Finalizada Exitosamente.")

if __name__ == '__main__':
    setup()
