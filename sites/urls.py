from rest_framework import routers
from .views import SiteViewSet, ZoneViewSet
from django.urls import path, include

router = routers.DefaultRouter()

router.register('sites', SiteViewSet),
router.register('zones', ZoneViewSet)


urlpatterns =  [
    path('api/', include(router.urls)),

]
