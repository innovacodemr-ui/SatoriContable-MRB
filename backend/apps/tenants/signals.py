from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Client
import requests

@receiver(post_save, sender=Client)
def fetch_company_info(sender, instance, created, **kwargs):
    if instance.nit and (created or kwargs.get('update_fields') and 'nit' in kwargs.get('update_fields')):
        # Make a request to an external API (e.g., RUES or a scraper)
        # to fetch company information based on the NIT.
        # This is a placeholder for the actual implementation.
        try:
            # I will use a public API for now, this should be replaced with a real RUES/DIAN scraper or API
            response = requests.get(f"https://api.empresarioenlinea.com/v1/empresas/{instance.nit}")
            if response.status_code == 200:
                data = response.json()
                instance.legal_name = data.get("razon_social", "")
                # The API does not provide the RUT status, so I will leave it as is for now
                instance.save(update_fields=['legal_name'])
        except requests.exceptions.RequestException as e:
            # Handle exceptions (e.g., network errors, invalid NIT)
            print(f"Error fetching company info: {e}")
