from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    Discipline, Categorie, Evenement, Resultat, Equipe, Joueur,
)
from .serializers import (
    DisciplineSerializer, CategorieSerializer,
    ResultatSerializer, EquipeSerializer, JoueurSerializer,
    EvenementSerializer,
)


# ---------------------------------------------------------------------------
# Permissions personnalisées
# ---------------------------------------------------------------------------
class IsAdminPersonnel(permissions.BasePermission):
    """Seuls les membres du personnel (ADMIN ou SUPERADMIN) peuvent écrire."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        return getattr(request.user, 'role', None) in ('ADMIN', 'SUPERADMIN')


class IsSuperadminPersonnel(permissions.BasePermission):
    """Permission réservée au SUPERADMIN (actions sensibles)."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'role', None) == 'SUPERADMIN'
        )


# ---------------------------------------------------------------------------
# Disciplines & Catégories
# ---------------------------------------------------------------------------
class DisciplineViewSet(viewsets.ModelViewSet):
    """
    CRUD des disciplines :
    - Lecture (list, retrieve, categories) : publique, même anonyme
    - Écriture : personnel (ADMIN ou SUPERADMIN)
    - export_disciplines : superadmin uniquement
    """
    queryset = Discipline.objects.all()
    serializer_class = DisciplineSerializer
    ordering = ['nom']
    search_fields = ['nom']

    def get_permissions(self):
        if self.action == 'export_disciplines':
            permission_classes = [IsSuperadminPersonnel]
        elif self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminPersonnel]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]

    @action(detail=True, methods=['get'], url_path='categories')
    def categories(self, request, pk=None):
        """GET /api/disciplines/1/categories/ — publique."""
        discipline = self.get_object()
        categories = Categorie.objects.filter(discipline=discipline)
        serializer = CategorieSerializer(categories, many=True)
        return Response(serializer.data)


class CategorieViewSet(viewsets.ModelViewSet):
    """
    CRUD des catégories : lecture publique, écriture réservée au personnel.
    """
    queryset = Categorie.objects.all().select_related('discipline')
    serializer_class = CategorieSerializer
    filterset_fields = ['discipline']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminPersonnel]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]


# ---------------------------------------------------------------------------
# Événements
# ---------------------------------------------------------------------------
class EvenementViewSet(viewsets.ModelViewSet):
    """
    CRUD des événements : lecture publique, écriture réservée au personnel.
    """
    queryset = Evenement.objects.all().select_related('site', 'categorie__discipline')
    serializer_class = EvenementSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminPersonnel]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]


# ---------------------------------------------------------------------------
# Résultats
# ---------------------------------------------------------------------------
class ResultatViewSet(viewsets.ModelViewSet):
    """
    CRUD des résultats :
    - Lecture publique avec filtrage (événement, compétiteur, équipe, joueur)
    - Écriture réservée au personnel ; le créateur est renseigné automatiquement
    """
    queryset = Resultat.objects.all().select_related(
        'evenement', 'competiteur', 'createur'
    )
    serializer_class = ResultatSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = [
        'evenement',
        'competiteur',
        'competiteur__equipe',
        'competiteur__joueur',
    ]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminPersonnel]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """Renseigne automatiquement l'admin connecté comme créateur."""
        serializer.save(createur=self.request.user)


# ---------------------------------------------------------------------------
# Équipes & Joueurs
# ---------------------------------------------------------------------------
class EquipeViewSet(viewsets.ModelViewSet):
    """CRUD des équipes : lecture publique, écriture réservée au personnel."""
    queryset = Equipe.objects.all()
    serializer_class = EquipeSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminPersonnel]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]

    @action(detail=True, methods=['get'], url_path='evenements')
    def evenements(self, request, pk=None):
        """GET /api/equipes/1/evenements/ — événements d'une équipe."""
        equipe = get_object_or_404(Equipe, pk=pk)
        evenements = equipe.evenements.all()
        data = [
            {
                'id': evenement.id,
                'titre': evenement.titre,
                'date': evenement.date,
                'heure': evenement.heure,
                'description': evenement.description,
            }
            for evenement in evenements
        ]
        return Response(data)


class JoueurViewSet(viewsets.ModelViewSet):
    """CRUD des joueurs : lecture publique, écriture réservée au personnel."""
    queryset = Joueur.objects.all()
    serializer_class = JoueurSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminPersonnel]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]
