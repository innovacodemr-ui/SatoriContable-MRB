import os
import sys
import django
from django.contrib.auth import get_user_model

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

User = get_user_model()

def create_admin():
    username = "admin"
    email = "admin@satori.com.co"
    password = "admin"
    
    if not User.objects.filter(username=username).exists():
        print(f"Creating superuser '{username}'...")
        User.objects.create_superuser(username, email, password)
        print(f"Superuser created. Login: {username} / {password}")
    else:
        print(f"Updating password for superuser '{username}'...")
        u = User.objects.get(username=username)
        u.set_password(password)
        u.save()
        print(f"Password updated. Login: {username} / {password}")

if __name__ == '__main__':
    create_admin()
