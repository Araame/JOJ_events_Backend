from django.contrib.auth.models import AbstractUser
from django.db import models

class Utilisateur(AbstractUser):
    CHOIX_ROLES = (
        ('superadmin', 'Super Administrateur'),
        ('admin', 'Administrateur'),
    )
    role = models.CharField(max_length=20, choices=CHOIX_ROLES, default='admin')
    telephone = models.CharField(max_length=15, blank=True, null=True)
    cree_le = models.DateTimeField(auto_now_add=True)
    mis_a_jour_le = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"