from django.db import models

class StatutNotification(models.TextChoices):
    LU = 'LU', 'Lu'
    NON_LU = 'NON_LU', 'Non lu'

class Notification(models.Model):
    spectateur = models.ForeignKey('paiements.Spectateur', on_delete=models.CASCADE, related_name='notifications')
    objet = models.CharField(max_length=255)
    contenu = models.TextField()
    date = models.DateField(auto_now_add=True)
    statut = models.CharField(
        max_length=10, 
        choices=StatutNotification.choices, 
        default=StatutNotification.NON_LU
    )
