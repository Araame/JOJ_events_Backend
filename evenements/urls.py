from rest_framework.routers import DefaultRouter
from .views import Evenements



from .views import DisciplineViewSet, CategorieViewSet

# evenements/urls.py
from django.urls import path, include
from .views import DisciplineViewSet, CategorieViewSet,  ResultatViewSet, JoueurViewSet, EquipeViewSet

router = DefaultRouter()
router.register(r'resultats', ResultatViewSet, basename='resultat')
router.register(r'disciplines', DisciplineViewSet, basename='discipline')
router.register(r'categories', CategorieViewSet, basename='categorie')
router.register(r'joueurs', JoueurViewSet, basename='joueur')
router.register(r'equipes', EquipeViewSet, basename='equipe')
router.register('events', Evenements, basename='events')



urlpatterns = [
    path('', include(router.urls)),
]
