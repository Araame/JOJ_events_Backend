from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models

class RolePersonnel(models.TextChoices):
    ADMIN = 'ADMIN', 'Administrateur'
    SUPERADMIN = 'SUPERADMIN', 'Super-administrateur'


class PermissionApp(models.TextChoices):
    JEUX = 'JEUX', 'Gestion des jeux'
    ACTUALITES = 'ACTUALITES', 'Gestion des actualites et résultats'
    UTILISATEURS = 'UTILISATEURS', 'Gestion des utilisateurs'
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
    permissions_app = models.JSONField(
        default=list,
        blank=True,
        help_text="Liste des permissions de l'utilisateur"
    )

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