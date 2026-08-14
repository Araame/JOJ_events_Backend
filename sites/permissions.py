from rest_framework import permissions
class IsAdminPersonnel(permissions.BasePermission):
    """
    Permission personnalisée : seuls les membres du personnel
    (ADMIN ou SUPERADMIN) peuvent effectuer des opérations d'écriture.
    Les spectateurs  ne peuvent que lire.
    """

    def has_permission(self, request, view):
        # Toute méthode de lecture (GET, HEAD, OPTIONS) est publique
        if request.method in permissions.SAFE_METHODS:
            return True

        # Les méthodes d'écriture exigent un personnel authentifié
        if not request.user or not request.user.is_authenticated:
            return False

        # Vérifier que l'utilisateur est du personnel (ADMIN ou SUPERADMIN)
        return getattr(request.user, 'role', None) in ('ADMIN', 'SUPERADMIN')
