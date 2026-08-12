from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models

class RolePersonnel(models.TextChoices):
    ADMIN = 'ADMIN', 'Administrateur'
    SUPERADMIN = 'SUPERADMIN', 'Super-administrateur'


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

    objects = PersonnelManager()

    def save(self, *args, **kwargs):
        # Garantir la cohérence role <-> is_superuser à chaque sauvegarde
        if self.is_superuser:
            self.role = RolePersonnel.SUPERADMIN
            self.is_staff = True
        super().save(*args, **kwargs)

class Admin(Personnel):
    class Meta: proxy = True

class Superadmin(Admin):
    class Meta: proxy = True