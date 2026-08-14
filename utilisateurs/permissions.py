# utilisateurs/permissions.py
from rest_framework.permissions import BasePermission
from .models import PermissionApp


class HasPermission(BasePermission):
    def __init__(self, permission_name):
        self.permission_name = permission_name

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return request.user.has_permission(self.permission_name)


class EvenementsPermission(HasPermission):
    def __init__(self):
        super().__init__(PermissionApp.EVENEMENTS)


class ZonesPermission(HasPermission):
    def __init__(self):
        super().__init__(PermissionApp.ZONES)


class ResultatsPermission(HasPermission):
    def __init__(self):
        super().__init__(PermissionApp.RESULTATS)


class BilletsPermission(HasPermission):
    def __init__(self):
        super().__init__(PermissionApp.BILLETS)


class PaiementsPermission(HasPermission):
    def __init__(self):
        super().__init__(PermissionApp.PAIEMENTS)


class ActualitesPermission(HasPermission):
    def __init__(self):
        super().__init__(PermissionApp.ACTUALITES)


class SitesPermission(HasPermission):
    def __init__(self):
        super().__init__(PermissionApp.SITES)


class NotificationsPermission(HasPermission):
    def __init__(self):
        super().__init__(PermissionApp.NOTIFICATIONS)


class UtilisateursPermission(HasPermission):
    def __init__(self):
        super().__init__(PermissionApp.UTILISATEURS)


class DisciplinesPermission(HasPermission):
    def __init__(self):
        super().__init__(PermissionApp.DISCIPLINES)


class CategoriesPermission(HasPermission):
    def __init__(self):
        super().__init__(PermissionApp.CATEGORIES)


class CompetiteursPermission(HasPermission):
    def __init__(self):
        super().__init__(PermissionApp.COMPETITEURS)


class EstSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_superuser