from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from .serializers import SiteSerializer
from .models import Site
from .pagination import SitePagination
from .permissions import IsAdminPersonnel
from .filters import SiteFilter


class SiteViewSet(viewsets.ModelViewSet):
    """ModelViewSet pour Site avec filtres avancés"""

    queryset = Site.objects.all()
    serializer_class = SiteSerializer
    pagination_class = SitePagination
    permission_classes = [IsAdminPersonnel]

    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = SiteFilter  

    # Cherche dans les champs nom, ville, region du modèle Site
    search_fields = ['nom', 'ville', 'region']


    
    