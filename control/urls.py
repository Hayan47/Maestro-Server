from django.urls import path

from . import views


urlpatterns = [
    path('', views.test_control, name='test_control'),
]