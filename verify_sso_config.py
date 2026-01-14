import os
import django
from django.conf import settings
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

def verify():
    print("--- VERIFICATION START ---")
    try:
        site = Site.objects.get(id=1)
        print(f"Site ID 1: {site.domain} ({site.name})")
    except Exception as e:
        print(f"Site Error: {e}")

    try:
        app = SocialApp.objects.get(provider='google')
        print(f"Google App: {app.name} (Client ID ends with ...{app.client_id[-5:]})")
        print(f"Google App Sites: {[s.domain for s in app.sites.all()]}")
    except Exception as e:
        print(f"Google App Error: {e}")
    print("--- VERIFICATION END ---")

if __name__ == '__main__':
    verify()
