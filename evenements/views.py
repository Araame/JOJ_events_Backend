from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Discipline, Categorie
from .serializers import DisciplineSerializer, CategorieSerializer
from django_filters.rest_framework import DjangoFilterBackend



from rest_framework.viewsets import ModelViewSet
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Resultat, Evenement, Equipe,  Joueur
from .serializers import ResultatSerializer, EquipeSerializer, JoueurSerializer


# Critères d'acceptation
# GET /api/résultats/ retourne la liste des résultats
# GET /api/résultats/{id}/ retourne le détail
# GET /api/résultats/{id}/équipe/ retourne les événements associés
# Les données incluent évènement, dicipline, équipe si disponible

class EquipeViewSet(ModelViewSet):
    queryset= Equipe.objects.all()
    serializer_class= EquipeSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes=[permissions.AllowAny]
        else:
            permission_classes=[permissions.IsAdminUser]
        return[permission() for permission in permission_classes]  
    @action(detail=True, methods=['get'], url_path='evenements')  

    def evenements(self, request, id=None):
        """
        afficher les événements auxquels une équipe participe
        """    
        equipe= get_object_or_404(Equipe, id=id)

        evenements= equipe.evenements.all()

        data=[
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
    queryset= Joueur.objects.all()
    serializer_class= JoueurSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes=[permissions.AllowAny]
        else:
            permission_classes=[permissions.IsAdminUser]
        return[permission() for permission in permission_classes]        
        

class ResultatViewSet(ModelViewSet):
   queryset=Resultat.objects.all().select_related(
   'evenement',
   'competiteur',
   'createur')


   serializer_class= ResultatSerializer
   
   # Configuration du filtrage avec django-filter 
   filter_backends = [DjangoFilterBackend]
   filterset_fields = ['evenement', 
                     'competiteur',
                     'competiteur__equipe', # GET /api/resultats/?competiteur__equipe__1
                     'competiteur__joueur', # heritage
                     ]


   def get_permissions(self):


       if self.action in ['list', 'retrieve']:
           permission_classes=[permissions.AllowAny]
       else:
           permission_classes=[permissions.IsAdminUser]


       return [permission() for permission in permission_classes] 


   def perform_create(self, serializer):
       """
       Appelée lors de la création (POST).
       Ajoute automatiquement l'utilisateur connecté comme createur.
       """  
       serializer.save(createur=self.request.user)


       # 2.4 Endpoint personnalisé : résultats par événement
#    @action(detail=False, methods=['get'], url_path='evenement/(?P<id>[^/.]+)')   
#    def get_resultat_by_event(self, request, id=None):
#        """
#        Endpoint personnalisé : GET /api/resultats/evenement/1/
#        Récupère tous les résultats d'un événement spécifique.
#        """
#        evenement=get_object_or_404(Evenement, id=id)
#        results=self.queryset.filter(evenement=evenement)
#        serializer= self.get_serializer(results, many=True)
#        return Response(serializer.data)

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

class CategorieViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API publique en lecture seule pour consulter les catégories d'épreuves.
    """
    queryset = Categorie.objects.all().select_related('discipline')
    serializer_class = CategorieSerializer
    
    # Filtrage par discipline 
    filterset_fields = ['discipline']