from rest_framework.viewsets import ModelViewSet
from .models import Actualite
from django_filters.rest_framework import DjangoFilterBackend
from .serializer import ActualiteSerializer
from rest_framework import permissions

class ActualiteViewset(ModelViewSet):
    queryset= Actualite.objects.all().select_related(
        'evenement_lie',
        'auteur'
    )
    serializer_class= ActualiteSerializer

     # endpoints personnalises
    filter_backends=[DjangoFilterBackend]
    filterset_fields=[
        'evenement_lie',
        'auteur'
    ] 

    # les permissions
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes=[permissions.AllowAny]
        else:
            permission_classes=[permissions.IsAdminUser]
        return[permission() for permission in permission_classes]    

    # recuperer le user connecte comme createur de l'actualites
    def perform_create(self, serializer):
        serializer.save(auteur=self.request.user)
       