import os
import django
import sys

# Add the project root to the python path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from allauth.socialaccount.models import SocialAccount

User = get_user_model()
emails = ['mario.rodriguez1130@gmail.com', 'innovacode.mr@gmail.com']

for email in emails:
    print(f"--- Checking {email} ---")
    try:
        u = User.objects.get(email=email)
        print(f"User found: ID={u.id}, Username='{u.username}'")
        socials = SocialAccount.objects.filter(user=u)
        if socials.exists():
            print(f"Linked Social Accounts: {[s.provider for s in socials]}")
        else:
            print("NO Social Accounts linked.")
    except User.DoesNotExist:
        print("User NOT found in database.")
