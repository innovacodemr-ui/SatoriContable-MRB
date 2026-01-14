import os
import django
from django.conf import settings
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

def setup():
    # 1. Configure Site
    print("Configuring Site...")
    try:
        site, created = Site.objects.get_or_create(id=1)
        site.domain = 'innovacode-mrb.com'
        site.name = 'Cooperativa MRB'
        site.save()
        print(f"SUCCESS: Site ID 1 set to {site.domain}")
    except Exception as e:
        print(f"ERROR configuring Site: {e}")

    # 2. Configure Google SocialApp
    print("Configuring Google SocialApp...")
    client_id = os.environ.get('GOOGLE_CLIENT_ID', '__GOOGLE_CLIENT_ID__')
    secret = os.environ.get('GOOGLE_SECRET', '__GOOGLE_SECRET__')
    
    try:
        app, created = SocialApp.objects.get_or_create(
            provider='google',
            defaults={
                'name': 'Google Auth',
                'client_id': client_id,
                'secret': secret,
            }
        )
        if not created:
            app.client_id = client_id
            app.secret = secret
            app.name = 'Google Auth'
            app.save()
            print("Updated existing Google App.")
        else:
            print("Created new Google App.")
        
        # Link to Site
        app.sites.add(site)
        print("Linked Google App to Site ID 1.")
        
    except Exception as e:
        print(f"ERROR configuring SocialApp: {e}")

if __name__ == '__main__':
    setup()
