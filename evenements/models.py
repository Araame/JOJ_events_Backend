from django.db import models
from django.conf import settings

class Pays(models.TextChoices):
  SENEGAL = 'SN', 'Sénégal'
  FRANCE = 'FR', 'France'
  USA = 'US', 'États-Unis'
  JAPON = 'JP', 'Japon'
  AUTRE = 'OT', 'Autre'

class Discipline(models.Model):
  nom = models.CharField(max_length=100)
  regle = models.TextField(blank=True)
  accessibilite = models.TextField(blank=True)


class Categorie(models.Model):
  discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE, related_name='categories')
  nom = models.CharField(max_length=100)
  description = models.TextField(blank=True)


class Competiteur(models.Model):
  categorie = models.ForeignKey(Categorie, on_delete=models.CASCADE, related_name='competiteurs')
  statut = models.BooleanField(default=True)
  pays = models.CharField(max_length=2, choices=Pays.choices)
  image = models.ImageField(upload_to='competiteurs/',blank=True, null=True)


class Joueur(Competiteur):
  nom = models.CharField(max_length=100)
  prenom = models.CharField(max_length=100)


class Equipe(Competiteur):
  nom = models.CharField(max_length=100)

class Evenement(models.Model):
  titre = models.CharField(max_length=255)
  date = models.DateField()
  heure = models.TimeField()
  site = models.ForeignKey('sites.Site', on_delete=models.CASCADE, related_name='evenements')
  categorie = models.ForeignKey(Categorie, on_delete=models.CASCADE, related_name='evenements')
  description = models.TextField(blank=True)
  image = models.ImageField(upload_to='evenements/', blank=True, null=True)


class Resultat(models.Model):
    evenement = models.ForeignKey(Evenement, on_delete=models.CASCADE, related_name='resultat')
    score = models.CharField(max_length=255)
    createur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,  related_name='resultats_crees')
    competiteur = models.ForeignKey(Competiteur, on_delete=models.CASCADE, blank=True, null=True)

