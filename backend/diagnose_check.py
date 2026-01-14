import os
import sys
import django
from django.core.management import call_command
from io import StringIO
import traceback

# Mock sys.argv to allow TenantAwareManager bypass if check is in list
sys.argv = ['manage.py', 'check']
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

try:
    django.setup()
    
    out = StringIO()
    err = StringIO()
    
    print("Running system check...")
    try:
        call_command('check', stdout=out, stderr=err)
        print("Check passed!")
    except Exception as e:
        print("\n======== CAPTURED STDERR ========")
        print(err.getvalue())
        print("=================================")
        print(f"\n======== SYSTEM CHECK ERROR ========\n{e}\n====================================")
        try:
             # Try to access internal errors list often present in SystemCheckError
             if hasattr(e, 'messages'):
                 print("\nDetailed Messages:")
                 for msg in e.messages:
                     print(f"- {msg}")
        except:
            pass
        # traceback.print_exc()

except Exception as e:
    print("FATAL ERROR IN SETUP:")
    traceback.print_exc()
