from . import views

from django.urls import path

urlpatterns = [
    path("", views.trade_up, name="trade_up_home")
]
