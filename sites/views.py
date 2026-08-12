from rest_framework import viewsets
from .serializers import ZoneSerializer, SiteSerializer
from .models import Site, Zone
from .pagination import SitePagination


class SiteViewSet(viewsets.ModelViewSet):
    """ModelViewSet pour Site"""

    queryset = Site.objects.all()
    serializer_class = SiteSerializer
    pagination_class = SitePagination


class ZoneViewSet(viewsets.ModelViewSet):
    """ModelViewSet pour Zone"""
    
    queryset = Zone.objects.all()
    serializer_class = ZoneSerializer