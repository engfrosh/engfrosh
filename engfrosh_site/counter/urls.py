from . import views

from django.urls import path

urlpatterns = [
    path("", views.counter, name="counter_home")
]
