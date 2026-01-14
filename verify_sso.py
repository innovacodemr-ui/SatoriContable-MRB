from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

print("--- SATORI SSO DIAGNOSTIC ---")

try:
    # 1. Verify Site
    site = Site.objects.get(id=1)
    print(f"[OK] Site Found: {site.domain} (ID: 1)")

    # 2. Verify SocialApp
    google_app = SocialApp.objects.filter(provider='google').first()
    if not google_app:
        print("[FAIL] Google SocialApp MISSING in Database!")
        print("       Run 'setup_sso_db.py' or create it manually via Admin.")
    else:
        print(f"[OK] Google App Found: {google_app.name}")
        
        # 3. Verify Link
        if site in google_app.sites.all():
            print("[OK] App is linked to Site 1")
        else:
            print("[WARN] App NOT linked to Site 1. Linking now...")
            google_app.sites.add(site)
            google_app.save()
            print("[FIXED] App linked to Site 1")

except Exception as e:
    print(f"[CRITICAL] Error: {e}")
