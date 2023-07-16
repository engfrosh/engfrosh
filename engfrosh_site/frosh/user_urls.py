from django.urls import path

from . import views

urlpatterns = [
    path('', views.user_home, name="user_home"),
    path('inclusivity_public', views.inclusivity_public, name="inclusivity_public"),
    path('inclusivity_private', views.inclusivity_private, name="inclusivity_private"),
]
