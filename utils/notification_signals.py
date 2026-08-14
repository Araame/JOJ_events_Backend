"""
Module générique de notification back-office.
Notifie les superadmins à chaque CRUD sur n'importe quel modèle.

Utilisation (dans chaque apps.py) :
    register_crud_notifications(Actualite, 'Actualité')
    register_crud_notifications(Site, 'Site')
"""
from django.conf import settings
from django.db.models.signals import post_save, pre_delete
from notifications.models import Notification, DestinataireType




def _notifier_superadmins(modele_nom, action, objet_str):
    """Crée une notification pour tous les superadmins."""
    from django.contrib.auth import get_user_model

    superadmins = get_user_model().objects.filter(role='SUPERADMIN')

    for superadmin in superadmins:
        Notification.objects.create(
            destinataire_type=DestinataireType.PERSONNEL,
            personnel=superadmin,
            objet=f"[{modele_nom}] {action} : {objet_str}",
            contenu=(
                f"Un membre du personnel a effectué l'action '{action}' "
                f"sur le {modele_nom} '{objet_str}'."
            ),
        )


def register_crud_notifications(model_class, modele_nom):
    """
    Enregistre les signaux CRUD (création, modification, suppression)
    pour un modèle donné.

    Args:
        model_class: la classe du modèle (ex: Actualite, Site)
        modele_nom: le nom lisible (ex: 'Actualité', 'Site')
    """

    def on_post_save(sender, instance, created, **kwargs):
        action = 'CRÉATION' if created else 'MODIFICATION'
        _notifier_superadmins(modele_nom, action, str(instance))

    def on_pre_delete(sender, instance, **kwargs):
        _notifier_superadmins(modele_nom, 'SUPPRESSION', str(instance))

    post_save.connect(on_post_save, sender=model_class)   # ← syntaxe correcte
    pre_delete.connect(on_pre_delete, sender=model_class) # ← syntaxe correcte

    return on_post_save, on_pre_delete
