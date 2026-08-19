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


@receiver(post_save, sender=Payment)
def on_payment_reussi(sender, instance, created, **kwargs):
    """
    Notifie uniquement lors d'une transition INTENTIONNELLE vers REUSSI.
    Le flag statut_mis_a_jour est auto-éteint après usage : une
    re-sauvegarde ultérieure ne renvoie jamais de doublon.
    """
    if instance.statut != StatutPaiement.REUSSI:
        return
    if created:
        return

    # Consommer le flag (True la 1re fois, puis il disparaît)
    intentionnelle = getattr(instance, 'statut_mis_a_jour', False)
    if intentionnelle:
        delattr(instance, 'statut_mis_a_jour')   # ← éteindre le flag
    else:
        return   # pas une transition intentionnelle → silence

    # --- Envoi des notifications ---
    billet = instance.billet
    spectateur = billet.spectateur
    evenement = billet.evenement
    transaction_obj = billet.transaction

    objet = "JOJ Dakar 2026 — Confirmation de paiement"
    contenu = (
        f"Bonjour {spectateur.prenom},\n\n"
        f"Votre paiement de {instance.montant} FCFA "
        f"(méthode : {instance.get_methode_display()}) a réussi.\n\n"
        f"Transaction n° {transaction_obj.numero_transaction if transaction_obj else 'N/A'}\n"
        f"Événement : {evenement.titre}\n"
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

    _notifier_superadmins(
        objet=f"[Paiement] Paiement réussi — {spectateur}",
        contenu=(
            f"Le spectateur {spectateur} a payé "
            f"{instance.montant} FCFA via {instance.get_methode_display()} "
            f"pour '{evenement.titre}'. "
            f"Billet validé : {billet.code_unique}."
        ),
    )
