from django.contrib.sites.models import Site
import os

try:
    site = Site.objects.get(id=1)
    site.domain = 'innovacode-mrb.com'
    site.name = 'Satori MRB'
    site.save()
    print(f"SUCCESS: Site updated to {site.domain}")
except Site.DoesNotExist:
    site = Site.objects.create(id=1, domain='innovacode-mrb.com', name='Satori MRB')
    print(f"SUCCESS: Site created {site.domain}")
except Exception as e:
    print(f"ERROR updating site: {e}")

# Also ensure SocialApp exists just in case (hybrid approach)
try:
    from allauth.socialaccount.models import SocialApp
    client_id = os.environ.get('GOOGLE_CLIENT_ID')
    secret = os.environ.get('GOOGLE_SECRET')
    
    if client_id and secret:
        app, created = SocialApp.objects.update_or_create(
            provider='google',
            defaults={
                'name': 'Google SSO',
                'client_id': client_id,
                'secret': secret,
            }
        )
        app.sites.add(site)
        print(f"SUCCESS: SocialApp configured for {app.provider}")
except Exception as e:
    print(f"ERROR updating SocialApp from Env: {e}")
