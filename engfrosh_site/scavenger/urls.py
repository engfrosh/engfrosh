"""URLS for the scavenger pages."""

from . import views
from django.urls import path
from django.views.generic import RedirectView

urlpatterns = [
    path('', views.index, name="scavenger_index"),
    path('puzzle/', RedirectView.as_view(pattern_name="scavenger_index", permanent=False)),
    path('puzzle//', RedirectView.as_view(pattern_name="scavenger_index", permanent=False)),
    path('puzzle/<slug:slug>/', views.puzzle_view),
    path("puzzle/<slug:slug>/verification_photo/", views.puzzle_photo_verification_view),
    path("stream_completed", views.stream_view)
]
