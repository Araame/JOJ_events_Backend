from django.db import models
from django.conf import settings

class Actualite(models.Model):
    titre = models.CharField(max_length=255)
    description = models.TextField()
    auteur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    image = models.ImageField(upload_to='actualites/', blank=True, null=True)
    brouillon = models.BooleanField(default=True)
    date_publication = models.DateTimeField(blank=True, null=True)
    evenement_lie = models.ForeignKey('evenements.Evenement', on_delete=models.CASCADE, related_name='actualites')