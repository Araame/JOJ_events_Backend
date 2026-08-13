from django.db import models
from django.conf import settings

class DestinataireType(models.TextChoices):
    """ Distinction entre les deux flux de notifications """
    SPECTATEUR = 'SPECTATEUR', 'Spectateur'
    PERSONNEL = 'PERSONNEL', 'Personnel'


class StatutNotification(models.TextChoices):
    LU = 'LU', 'Lu'
    NON_LU = 'NON_LU', 'Non lu'

class Notification(models.Model):
    """
    Notification unifiée pour JOJ_EVENT.
    - SPECTATEUR : envoyée après paiement d'un billet (email + dashboard).
    - PERSONNEL : envoyée au superadmin sur chaque CRUD effectué par un admin.
    """
    # Qui reçoit la notification ?
    destinataire_type = models.CharField(
        max_length=12,
        choices=DestinataireType.choices,
        default=DestinataireType.SPECTATEUR
    )

    # Destinataire (optionnel selon le flux)
    spectateur = models.ForeignKey(
        'paiements.Spectateur',
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True, blank=True,
        help_text="Obligatoire si destinataire_type = SPECTATEUR"
    )
    personnel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications_backoffice',
        null=True, blank=True,
        help_text="Obligatoire si destinataire_type = PERSONNEL"
    )

    # La transaction liée (uniquement pour le flux spectateur)
    transaction = models.ForeignKey(
        'paiements.Transaction',
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True, blank=True,
        help_text="Obligatoire si destinataire_type = SPECTATEUR"
    )

    objet = models.CharField(max_length=255)
    contenu = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(
        max_length=10,
        choices=StatutNotification.choices,
        default=StatutNotification.NON_LU
    )

    class Meta:
        ordering = ['-date']

    def __str__(self):
        if self.destinataire_type == DestinataireType.SPECTATEUR:
            return f"[Spectateur] {self.objet}"
        return f"[Back-office] {self.objet}"
