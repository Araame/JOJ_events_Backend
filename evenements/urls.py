from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DisciplineViewSet, CategorieViewSet

router = DefaultRouter()
router.register(r'disciplines', DisciplineViewSet, basename='discipline')
router.register(r'categories', CategorieViewSet, basename='categorie')

urlpatterns = [
    path('', include(router.urls)),
]