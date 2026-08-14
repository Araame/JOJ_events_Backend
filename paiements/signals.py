# paiements/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.core.mail import send_mail
from django.apps import apps

from .models import Payment, StatutPaiement
from notifications.models import Notification, DestinataireType


def _notifier_superadmins(objet, contenu):
    Personnel = apps.get_model(settings.AUTH_USER_MODEL)
    superadmins = Personnel.objects.filter(role='SUPERADMIN')
    for superadmin in superadmins:
        Notification.objects.create(
            destinataire_type=DestinataireType.PERSONNEL,
            personnel=superadmin,
            objet=objet,
            contenu=contenu,
        )


def _envoyer_confirmation_spectateur(payment):
    """Email + notification DB pour le spectateur (paiement réussi)."""
    billet = payment.billet
    spectateur = billet.spectateur
    transaction_obj = billet.transaction
    evenement = billet.evenement

    objet = "JOJ Dakar 2026 — Confirmation de paiement"
    contenu = (
        f"Bonjour {spectateur.prenom},\n\n"
        f"Votre paiement de {payment.montant} FCFA "
        f"(méthode : {payment.get_methode_display()}) a réussi.\n\n"
        f"Transaction n° {transaction_obj.numero_transaction}\n"
        f"Événement : {evenement}\n"
        f"Billet : {billet.get_type_billet_display()}\n"
        f"Code d'accès : {billet.code_unique}\n\n"
        f"Conservez ce code, il vous sera demandé à l'entrée du site.\n"
        f"Bienvenue aux JOJ Dakar 2026 !"
    )

    Notification.objects.create(
        destinataire_type=DestinataireType.SPECTATEUR,
        spectateur=spectateur,
        objet=objet,
        contenu=contenu,
    )

    try:
        send_mail(
            subject=objet,
            message=contenu,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[spectateur.email],
            fail_silently=True,
        )
    except Exception:
        pass


@receiver(post_save, sender=Payment)
def on_payment_reussi(sender, instance, created, **kwargs):
    """Notifie uniquement quand le statut devient (ou reste) REUSSI,
    mais pas lors de la création initiale en EN_COURS."""
    if instance.statut != StatutPaiement.REUSSI:
        return
    if created:
        return  # créé en EN_COURS dans la vue, on attend le passage à REUSSI

    _envoyer_confirmation_spectateur(instance)
    _notifier_superadmins(
        objet=f"[Paiement] Paiement réussi — {instance.billet.spectateur}",
        contenu=(
            f"Le spectateur {instance.billet.spectateur} a payé "
            f"{instance.montant} FCFA via {instance.get_methode_display()} "
            f"pour '{instance.billet.evenement}'. "
            f"Billet validé : {instance.billet.code_unique}."
        ),
    )