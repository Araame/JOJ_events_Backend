from rest_framework.routers import DefaultRouter
from .views import DisciplineViewSet, CategorieViewSet, Evenements, ResultatViewSet, JoueurViewSet, EquipeViewSet

# evenements/urls.py
from django.urls import path, include

router = DefaultRouter()
router.register(r'resultats', ResultatViewSet, basename='resultat')
router.register(r'disciplines', DisciplineViewSet, basename='discipline')
router.register(r'categories', CategorieViewSet, basename='categorie')
router.register(r'joueurs', JoueurViewSet, basename='joueur')
router.register(r'equipes', EquipeViewSet, basename='equipe')
router.register(r'evenements', Evenements, basename='evenements')

urlpatterns = [
    path('', include(router.urls)),
]