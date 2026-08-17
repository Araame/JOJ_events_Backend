# Import des filtres
import django_filters
from.models import Site
from rest_framework import viewsets
from .pagination import SitePagination
from .permissions import IsAdminPersonnel
from .serializers import SiteSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter



class SiteFilter(django_filters.FilterSet):
    """Filtres personnalisés pour les Sites"""
    
    # Filtre par ville (contient ou égal)
    ville = django_filters.CharFilter(lookup_expr='icontains')
    
    # Filtre par capacité minimale (>=)
    # Suppose que votre modèle Site a un champ 'capacite' ou 'capacity'
    capacite_min = django_filters.NumberFilter(field_name='capacite', lookup_expr='gte')

    class Meta:
        model = Site
        # On ne filtre pas par 'nom' ici car SearchFilter le gère mieux
        fields = {
            'ville': ['icontains'],
        }


class SiteViewSet(viewsets.ModelViewSet):
    """ModelViewSet pour Site avec filtres avancés"""

    queryset = Site.objects.all()
    serializer_class = SiteSerializer
    pagination_class = SitePagination
    permission_classes = [IsAdminPersonnel]

    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = SiteFilter  # Utilise notre classe de filtre personnalisée

    # 2. Backend de recherche (SearchFilter)
    # Cherche dans les champs nom, ville, region du modèle Site
    search_fields = ['nom', 'ville', 'region']

    # Optionnel : Permettre le tri
    # filter_backends.append(OrderingFilter)
    # ordering_fields = ['nom', 'ville', 'capacite', 'date_creation']
    
    def get_queryset(self):
        """
        Filtrage supplémentaire si nécessaire (ex: filtrage par Site parent si relation hiérarchique).
        """
        return super().get_queryset()

    # La méthode create/update reste gérée par le serializer et le ViewSet standard
    # Pas besoin de surcharger create() pour les filtres.