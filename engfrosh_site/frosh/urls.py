from django.urls import path

from . import views

urlpatterns = [
    path('coin/', views.coin_standings)
]
