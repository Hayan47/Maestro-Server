from django.contrib import admin
from django.urls import include, path



urlpatterns = [
    path("", include("authentication.urls")),
    path("api/control/", include("control.urls")),  
    path('admin/', admin.site.urls),
]
