from django.apps import AppConfig


class EvenementsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'evenements'

    def ready(self):
        from .models import Evenement, Resultat
        from utils.notification_signals import register_crud_notifications
        register_crud_notifications(Evenement, 'Événement')
        register_crud_notifications(Resultat, 'Résultat')
