from django.shortcuts import render
from rest_framework import viewsets
from .models import Evenement
from .serializers import EvenementSerializer,EvenementListSerializer

from .eventFiltre import EventFiltre
from django_filters.rest_framework import DjangoFilterBackend
from .pagination import EvenementPagination
from .permissions import IsAdminOrReadOnly

class Evenements(viewsets.ModelViewSet):
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
    # regle de filtrage
    filterset_class = EventFiltre
    #pagination
    pagination_class = EvenementPagination
        
        
    
    
