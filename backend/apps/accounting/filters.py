import django_filters
from apps.accounting.models import DianConcept

class DianConceptFilter(django_filters.FilterSet):
    dian_format = django_filters.NumberFilter(field_name='format')

    class Meta:
        model = DianConcept
        fields = ['dian_format']
