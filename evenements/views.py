
from rest_framework import viewsets, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Discipline, Categorie
from .serializers import DisciplineSerializer, CategorieSerializer

class DisciplineViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API publique en lecture seule pour consulter les disciplines olympiques.
    Un spectateur anonyme peut lister toutes les disciplines et voir leurs catégories.
    """
    queryset = Discipline.objects.all()
    serializer_class = DisciplineSerializer
    
    # Tri par ordre alphabétique
    ordering = ['nom']
    
    # Recherche par nom de discipline
    search_fields = ['nom']
    
    @action(detail=True, methods=['get'], url_path='categories')
    def categories(self, request, pk=None):
        """
        Action personnalisée pour lister les catégories d'une discipline spécifique.
        GET /api/disciplines/1/categories/
        """
        discipline = self.get_object()
        categories = Categorie.objects.filter(discipline=discipline)
        serializer = CategorieSerializer(categories, many=True)
        return Response(serializer.data)

    def get_permissions(self):
        """Toute action GET est publique, toute écriture exige l'authentification."""
        if self.request.method in permissions.SAFE_METHODS:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]



class CategorieViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API publique en lecture seule pour consulter les catégories d'épreuves.
    """
    queryset = Categorie.objects.all().select_related('discipline')
    serializer_class = CategorieSerializer
    
    # Filtrage par discipline 
    filterset_fields = ['discipline']

    def get_permissions(self):
        """Toute action GET est publique, toute écriture exige l'authentification."""
        if self.request.method in permissions.SAFE_METHODS:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

