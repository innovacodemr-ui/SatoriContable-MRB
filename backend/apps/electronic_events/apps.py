from django.apps import AppConfig

class ElectronicEventsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.electronic_events'
    verbose_name = "Eventos Electrónicos (RADIAN)"

    def ready(self):
        import apps.electronic_events.signals
