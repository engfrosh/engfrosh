"""URLS for the scavenger pages."""

from . import views
from django.urls import path
from django.views.generic import RedirectView

urlpatterns = [
    path('', views.index, name="scavenger_index"),
    path('puzzle/', RedirectView.as_view(pattern_name="scavenger_index", permanent=False)),
    path('puzzle/<slug:slug>/', views.puzzle_view)
]
