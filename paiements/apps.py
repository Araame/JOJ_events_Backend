from django.apps import AppConfig


class PaiementsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'paiements'

    def ready(self):
        # Charger les signaux au démarrage de l'application
        import paiements.signals  