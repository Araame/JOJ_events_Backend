from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificationBackofficeViewSet

router = DefaultRouter()
router.register(r'notifications-backoffice', NotificationBackofficeViewSet, basename='notification-backoffice')

urlpatterns = [
    path('', include(router.urls)),
]