from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ActualiteViewset


router = DefaultRouter()

router.register(r'actualites', ActualiteViewset, basename='actualite')
urlpatterns = [
    path("", include(router.urls))
]
