import os
import django
import sys

# Add the project root to the python path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()
superusers = User.objects.filter(is_superuser=True)

print("--- Superusers ---")
for su in superusers:
    print(f"Username: {su.username}, Email: {su.email}")
