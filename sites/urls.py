from rest_framework import routers
from .views import SiteViewSet
from django.urls import path, include

router = routers.DefaultRouter()

router.register('sites', SiteViewSet),


urlpatterns =  [
    path('api/', include(router.urls)),

]
