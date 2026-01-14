import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import RequestFactory
from rest_framework.test import APIRequestFactory, force_authenticate
from django.contrib.auth.models import User
from apps.accounting.views import DianConceptViewSet
from apps.accounting.models import DianFormat

def test_api():
    factory = APIRequestFactory()
    user = User.objects.first()
    if not user:
        print("No user found to authenticate")
        return

    # Create request
    # /accounting/dian-concepts/
    request = factory.get('/accounting/dian-concepts/')
    force_authenticate(request, user=user)

    view = DianConceptViewSet.as_view({'get': 'list'})
    
    try:
        response = view(request)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Response Data Count:", len(response.data)) # Pagination might change this structure
            if 'results' in response.data:
                print("Results count:", len(response.data['results']))
            else:
                print("Results count (flat):", len(response.data))
        else:
            print("Error Data:", response.data)
    except Exception as e:
        print(f"EXCEPTION: {e}")

if __name__ == '__main__':
    test_api()
