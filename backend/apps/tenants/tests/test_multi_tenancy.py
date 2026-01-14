from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from apps.tenants.models import Client
from apps.invoicing.models import Invoice

class MultiTenancyTest(TestCase):
    def setUp(self):
        # Create two clients (tenants)
        self.client1 = Client.objects.create(name="Client 1", nit="111.111.111-1")
        self.client2 = Client.objects.create(name="Client 2", nit="222.222.222-2")

        # Create a user for each client
        self.user1 = User.objects.create_user(username='user1', password='password1')
        self.user2 = User.objects.create_user(username='user2', password='password2')

        # Create an invoice for each client
        self.invoice1 = Invoice.objects.create(client=self.client1, number=1, total=100)
        self.invoice2 = Invoice.objects.create(client=self.client2, number=1, total=200)

        self.api_client = APIClient()

    def test_tenant_isolation(self):
        # Authenticate as user1 (associated with client1)
        self.api_client.force_authenticate(user=self.user1)

        # Set the tenant context to client1
        self.api_client.credentials(HTTP_X_CLIENT_ID=self.client1.id)

        # Try to access an invoice from client1 (should be successful)
        response = self.api_client.get(f'/api/invoicing/invoices/{self.invoice1.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], self.invoice1.id)

        # Try to access an invoice from client2 (should fail with 404 Not Found)
        response = self.api_client.get(f'/api/invoicing/invoices/{self.invoice2.id}/')
        self.assertEqual(response.status_code, 404)

    def test_no_tenant_context(self):
        # Authenticate as user1
        self.api_client.force_authenticate(user=self.user1)

        # Do not set the tenant context (X-Client-Id header)
        # The TenantAwareManager should raise an ImproperlyConfigured exception
        with self.assertRaises(ImproperlyConfigured):
            Invoice.objects.all()
