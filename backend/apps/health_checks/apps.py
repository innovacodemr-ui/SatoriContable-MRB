from django.apps import AppConfig


class HealthChecksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.health_checks'
    verbose_name = 'Health Checks'
