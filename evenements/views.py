from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Discipline, Categorie
from .serializers import DisciplineSerializer, CategorieSerializer

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


class IsSuperadminPersonnel(permissions.BasePermission):
    """
    Permission réservée au SUPERADMIN : utilisée pour les actions
    sensibles (ex: suppression massive, export des données).
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'role', None) == 'SUPERADMIN'
        )


class DisciplineViewSet(viewsets.ModelViewSet):
    """
    API des disciplines olympiques avec contrôle d'accès par rôles :
    - Spectateur  : lecture seule (list, retrieve, categories)
    - Admin : CRUD complet
    - Superadmin : CRUD complet + actions réservées

    Note : l'héritage ModelViewSet (au lieu de ReadOnlyModelViewSet)
    permet maintenant le CRUD complet.
    """
    queryset = Discipline.objects.all()
    serializer_class = DisciplineSerializer

    # Tri par ordre alphabétique
    ordering = ['nom']

    # Recherche par nom de discipline
    search_fields = ['nom']

    def get_permissions(self):
        """
        Contrôle d'accès selon le rôle :
        - Lecture : tout le monde (y compris anonyme)
        - Écriture (create/update/destroy) : personnel uniquement
        - Actions réservées superadmin : superadmin uniquement
        """
        # Les actions réservées au superadmin
        if self.action == 'export_disciplines':
            permission_classes = [IsSuperadminPersonnel]
        # Toute action d'écriture exige un personnel authentifié
        elif self.action in ['create', 'update', 'partial_update', 'delete', 'destroy']:
            permission_classes = [IsAdminPersonnel]
        # La lecture (list, retrieve, categories) est publique
        else:
            permission_classes = [permissions.AllowAny]

        return [permission() for permission in permission_classes]

    @action(detail=True, methods=['get'], url_path='categories')
    def categories(self, request, pk=None):
        """
        Action personnalisée pour lister les catégories d'une discipline.
        Accessible à tous : GET /api/disciplines/1/categories/
        """
        discipline = self.get_object()
        categories = Categorie.objects.filter(discipline=discipline)
        serializer = CategorieSerializer(categories, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='export',
            permission_classes=[IsSuperadminPersonnel])
    def export_disciplines(self, request):
        """
        Action réservée au SUPERADMIN : export complet des disciplines.
        GET /api/disciplines/export/
        """
        disciplines = self.get_queryset()
        serializer = DisciplineSerializer(disciplines, many=True)
        return Response({
            'total': disciplines.count(),
            'disciplines': serializer.data,
        })


class CategorieViewSet(viewsets.ModelViewSet):
    """
    API des catégories d'épreuves avec le même contrôle d'accès.
    - Lecture : publique
    - Écriture : personnel uniquement
    """
    queryset = Categorie.objects.all().select_related('discipline')
    serializer_class = CategorieSerializer

    # Filtrage par discipline
    filterset_fields = ['discipline']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminPersonnel]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]