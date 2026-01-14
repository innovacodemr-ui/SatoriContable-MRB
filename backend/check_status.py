import sys
import os
import django

sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.payroll.models import PayrollDocument

doc = PayrollDocument.objects.filter(employee__third_party__first_name__icontains='Ana').last()

if doc:
    print(f"Status: {doc.dian_status}")
    if doc.dian_response:
        print(f"DIAN Response Preview: {doc.dian_response[:200]}...")
    else:
        print("No DIAN response yet.")
else:
    print("Document not found for Ana.")
