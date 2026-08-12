from django.contrib.auth.models import AbstractUser
from django.db import models

class RolePersonnel(models.TextChoices):
    ADMIN = 'ADMIN', 'Administrateur'
    SUPERADMIN = 'SUPERADMIN', 'Super-administrateur'

class Personnel(AbstractUser):
    tel = models.CharField(max_length=20, blank=True, null=True)
    role = models.CharField(
        max_length=20, 
        choices=RolePersonnel.choices, 
        default=RolePersonnel.ADMIN
    )

class Admin(Personnel):
    class Meta: proxy = True

class Superadmin(Admin):
    class Meta: proxy = True