"""
URL configuration for joj_events project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Creation de l'objet Info (pour le projet)
swagger_info = openapi.Info(title="JOJ Events",default_version='v1',description="Documentation API pour les événements JOJ")

# Creation du schema view
schema_view = get_schema_view(swagger_info,public=True,permission_classes=(permissions.AllowAny,))

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api-auth/", include("rest_framework.urls")),

    # Configuration urls pour application SITE
    path('', include('sites.urls')),

    # Swagger UI
    path('swagger/', schema_view.with_ui('swagger'), name='swagger'),

    
]