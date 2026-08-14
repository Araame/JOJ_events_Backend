from rest_framework import viewsets
from .serializers import ZoneSerializer, SiteSerializer
from .models import Site, Zone
from .pagination import SitePagination
from.permissions import IsAdminPersonnel


class SiteViewSet(viewsets.ModelViewSet):
    """ModelViewSet pour Site"""

    queryset = Site.objects.all()
    serializer_class = SiteSerializer
    pagination_class = SitePagination
    permission_classes = [IsAdminPersonnel]





class ZoneViewSet(viewsets.ModelViewSet):
    """ModelViewSet pour Zone"""
    
    queryset = Zone.objects.all()
    serializer_class = ZoneSerializer
    permission_classes = [IsAdminPersonnel]
