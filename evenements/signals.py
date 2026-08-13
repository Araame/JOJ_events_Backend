from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver
from django.conf import settings
from notifications.models import Notification, DestinataireType
from .models import Discipline


def _notifier_superadmins(action, objet_str, details=""):
    """Crée une notification pour tous les superadmins."""
    Personnel = settings.AUTH_USER_MODEL
    superadmins = Personnel.objects.filter(role='SUPERADMIN')

    for superadmin in superadmins:
        Notification.objects.create(
            destinataire_type=DestinataireType.PERSONNEL,
            personnel=superadmin,
            objet=f"[Discipline] {action} : {objet_str}",
            contenu=(
                f"Un admin a effectué l'action '{action}' sur la discipline "
                f"'{objet_str}'. {details}"
            )
        )


@receiver(post_save, sender=Discipline)
def notifier_creation_discipline(sender, instance, created, **kwargs):
    """Notifie le superadmin après la création d'une discipline."""
    if created:
        _notifier_superadmins('CRÉATION', instance.nom)


@receiver(pre_delete, sender=Discipline)
def notifier_suppression_discipline(sender, instance, **kwargs):
    """Notifie le superadmin avant la suppression d'une discipline."""
    _notifier_superadmins('SUPPRESSION', instance.nom)


@receiver(post_save, sender=Discipline)
def notifier_modification_discipline(sender, instance, created, **kwargs):
    """Notifie le superadmin après la modification d'une discipline."""
    if not created:
        _notifier_superadmins('MODIFICATION', instance.nom)