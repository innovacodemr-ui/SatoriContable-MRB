import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.accounting.models import DianFormat, DianConcept

print("Checking Database...")
try:
    formats = DianFormat.objects.all()
    print(f"Total Formats: {formats.count()}")
    
    f1001 = DianFormat.objects.filter(code='1001').first()
    if f1001:
        print(f"Format 1001 found. ID: {f1001.id}")
        cnt = DianConcept.objects.filter(format=f1001).count()
        print(f"Concepts count for 1001: {cnt}")
        if cnt > 0:
            print("Concepts exist.")
        else:
            print("NO CONCEPTS FOUND for 1001.")
    else:
        print("Format 1001 NOT FOUND.")
except Exception as e:
    print(f"Error: {e}")
