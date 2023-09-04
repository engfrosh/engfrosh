from django.urls import path

from . import views

urlpatterns = [
    path('coin/', views.coin_standings, name="skash_standings"),
    path('mycoin', views.my_coin),
    path('my-skash', views.my_coin, name="my_skash")
]
