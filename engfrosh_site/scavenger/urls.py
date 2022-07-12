"""URLS for the scavenger pages."""

from . import views
from django.urls import path

urlpatterns = [
    path('', views.index, name="scavenger_index"),
    path('puzzle', views.puzzle_view)
]
