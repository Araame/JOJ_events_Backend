from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
<<<<<<< HEAD
    path("api-auth/", include("rest_framework.urls")),
    path('api/', include('evenements.urls')),
=======
    path('api/', include('evenements.urls')),  
    path("api-auth/", include("rest_framework.urls"))
>>>>>>> 125175b42cab4a2c099466af284e09eeae3365fb

]


