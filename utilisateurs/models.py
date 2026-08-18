from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models

class RolePersonnel(models.TextChoices):
    ADMIN = 'ADMIN', 'Administrateur'
    SUPERADMIN = 'SUPERADMIN', 'Super-administrateur'


class PermissionApp(models.TextChoices):
    EVENEMENTS = 'EVENEMENTS', 'Gestion des evenements'
    ZONES = 'ZONES', 'Gestion des zones'
    RESULTATS = 'RESULTATS', 'Gestion des resultats'
    BILLETS = 'BILLETS', 'Gestion des billets'
    PAIEMENTS = 'PAIEMENTS', 'Gestion des paiements'
    ACTUALITES = 'ACTUALITES', 'Gestion des actualites'
    SITES = 'SITES', 'Gestion des sites'
    NOTIFICATIONS = 'NOTIFICATIONS', 'Gestion des notifications'
    UTILISATEURS = 'UTILISATEURS', 'Gestion des utilisateurs'
    DISCIPLINES = 'DISCIPLINES', 'Gestion des disciplines'
    CATEGORIES = 'CATEGORIES', 'Gestion des categories'
    COMPETITEURS = 'COMPETITEURS', 'Gestion des competiteurs'
    TOUT = 'TOUT', 'Toutes les permissions'


class PersonnelManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields['role'] = RolePersonnel.SUPERADMIN
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return super().create_superuser(username, email, password, **extra_fields)


class Personnel(AbstractUser):
    tel = models.CharField(max_length=20, blank=True, null=True)
    role = models.CharField(
        max_length=20,
        choices=RolePersonnel.choices,
        default=RolePersonnel.ADMIN
    )
    # permissions_app = models.JSONField(
    #     default=list,
    #     blank=True,
    #     help_text="Liste des permissions de l'utilisateur"
    # )

    objects = PersonnelManager()

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = RolePersonnel.SUPERADMIN
            self.is_staff = True
            self.permissions_app = [PermissionApp.TOUT]
        super().save(*args, **kwargs)

    def has_permission(self, permission_name):
        if self.is_superuser or self.role == RolePersonnel.SUPERADMIN:
            return True
        if PermissionApp.TOUT in self.permissions_app:
            return True
        return permission_name in self.permissions_app


class Admin(Personnel):
    class Meta: proxy = True


class Superadmin(Admin):
    class Meta: proxy = True