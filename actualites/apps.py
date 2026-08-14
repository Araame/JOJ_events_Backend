from django.apps import AppConfig


class ActualitesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'actualites'

    def ready(self):
        from .models import Actualite
        from utils.notification_signals import register_crud_notifications
        register_crud_notifications(Actualite, 'Actualité')
