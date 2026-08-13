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
    path('api/', include('evenements.urls')),  
    # path("api-auth/", include("rest_framework.urls")),
    path('api/', include("actualites.urls")),


    # Configuration urls pour application SITE
    path('', include('sites.urls')),

    # Swagger UI
    path('swagger/', schema_view.with_ui('swagger'), name='swagger'),

   
    

   
]
