from django.apps import AppConfig


class SitesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sites'

    def ready(self):
        from .models import Site, Zone
        from utils.notification_signals import register_crud_notifications
        register_crud_notifications(Site, 'Site')
        register_crud_notifications(Zone, 'Zone')
