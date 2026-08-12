from rest_framework.routers import DefaultRouter
from .views import Evenements

router = DefaultRouter()

router.register('events', Evenements, basename='events')

urlpatterns = router.urls