from django.db import models

class Site(models.Model):
  nom= models.CharField(max_length=255)
  capacite = models.PositiveIntegerField()
  description = models.TextField(blank=True)
  service = models.TextField(blank=True)
  image = models.ImageField(upload_to='sites/', blank=True, null=True)
  latitude = models.FloatField(blank=True, null=True)
  longitude = models.FloatField(blank=True, null=True)
  ville = models.CharField(max_length=100)
  region = models.CharField(max_length=100)

  def __str__(self):
    return self.nom


class Zone(models.Model):
  site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='zones')
  nom = models.CharField(max_length=100)
  capacite = models.PositiveIntegerField()

  def __str__(self):
    return f"{self.nom} - {self.site.nom}"


