from rest_framework.permissions import BasePermission
from utilisateurs.models import RolePersonnel

class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method  in ['GET','HEAD','OPTIONS']:
            return True
        return(
            request.user.Is_authenticated 
            and request.user.role in [RolePersonnel.ADMIN,RolePersonnel.SUPERADMIN]
        )

