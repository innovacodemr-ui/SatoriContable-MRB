from django.contrib.sites.models import Site
try:
    site = Site.objects.get(id=1)
    site.domain = 'innovacode-mrb.com'
    site.name = 'Satori MRB'
    site.save()
    print(f"SUCCESS: Site updated to {site.domain}")
except Exception as e:
    print(f"ERROR: {e}")
