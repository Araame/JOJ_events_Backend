from rest_framework import viewsets, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from .models import Discipline, Categorie, Resultat, Evenement, Equipe, Joueur
from .serializers import (
    DisciplineSerializer,
    CategorieSerializer,
    ResultatSerializer,
    EquipeSerializer,
    JoueurSerializer,
    EvenementSerializer,
    EvenementListSerializer,
)
from .eventFiltre import EventFiltre
from .pagination import EvenementPagination


class IsAdminPersonnel(permissions.BasePermission):
    """Seuls les membres du personnel (ADMIN ou SUPERADMIN) peuvent écrire."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        return (
            request.user.is_staff
            or request.user.is_superuser
            or getattr(request.user, 'role', None) in ('ADMIN', 'SUPERADMIN')
        )


class IsSuperadminPersonnel(permissions.BasePermission):
    """Permission réservée au SUPERADMIN (actions sensibles)."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (request.user.is_superuser or getattr(request.user, 'role', None) == 'SUPERADMIN')
        )


# ---------------------------------------------------------------------------
# Disciplines & Catégories
# ---------------------------------------------------------------------------
class DisciplineViewSet(viewsets.ModelViewSet):
    """
    CRUD des disciplines :
    - Lecture (list, retrieve, categories) : publique
    - Écriture (create, update, destroy) : personnel authentifié
    """
    queryset = Discipline.objects.all()
    serializer_class = DisciplineSerializer
    ordering = ['nom']
    search_fields = ['nom']

    def get_permissions(self):
        # 1. Action spécifique superadmin
        if self.action == 'export_disciplines':
            permission_classes = [IsSuperadminPersonnel]
        elif self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated]
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




# ---------------------------------------------------------------------------
# Résultats
# ---------------------------------------------------------------------------

class CategorieViewSet(viewsets.ModelViewSet):
    """
    CRUD des résultats :
    - Lecture publique avec filtrage (événement, compétiteur, équipe, joueur)
    - Écriture réservée au personnel ; le créateur est renseigné automatiquement
    """
    queryset = Resultat.objects.all().select_related(
        'evenement',
        'competiteur',
        'createur',
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
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """Ajoute automatiquement l'utilisateur connecté comme créateur."""
        serializer.save(createur=self.request.user)


# ---------------------------------------------------------------------------
# Équipes & Joueurs
# ---------------------------------------------------------------------------
class EquipeViewSet(ModelViewSet):
    queryset = Equipe.objects.all().select_related('categorie')
    serializer_class = EquipeSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    @action(detail=True, methods=['get'], url_path='evenements')
    def evenements(self, request, pk=None):
        """Événements auxquels une équipe participe."""
        equipe = get_object_or_404(Equipe, pk=pk)
        evenements = Evenement.objects.filter(categorie=equipe.categorie)
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


class JoueurViewSet(ModelViewSet):
    queryset = Joueur.objects.all().select_related('categorie')
    serializer_class = JoueurSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]



from django.shortcuts import render
from rest_framework import viewsets
from .models import Evenement
from .serializers import EvenementSerializer,EvenementListSerializer

from .eventFiltre import EventFiltre
from django_filters.rest_framework import DjangoFilterBackend
from .pagination import EvenementPagination
from .permissions import IsAdminOrReadOnly

class EvenementViewSet(viewsets.ModelViewSet):
    queryset = Evenement.objects.all()
    def get_serializer_class(self):
        #get
        if self.action =='list':
            return EvenementListSerializer
        # POST, GET détail, PUT, PATCH
        return EvenementSerializer
    
    
    
    permission_classes = [IsAdminOrReadOnly]
    #systeme de filtrage
    filter_backends = [DjangoFilterBackend]
    filterset_class = EventFiltre
    pagination_class = EvenementPagination

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]