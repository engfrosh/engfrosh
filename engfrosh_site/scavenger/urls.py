"""URLS for the scavenger pages."""

from . import views
from django.urls import path
from django.views.generic import RedirectView

urlpatterns = [
    path('', views.index, name="scavenger_index"),
    path('puzzle/', RedirectView.as_view(pattern_name="scavenger_index", permanent=False)),
    path('puzzle//', RedirectView.as_view(pattern_name="scavenger_index", permanent=False)),
    path('puzzle/<slug:slug>/', views.puzzle_view, name="view_puzzle"),
    path("puzzle/<slug:slug>/verification_photo/", views.puzzle_photo_verification_view, name="verify_puzzle"),
    path("stream_completed", views.stream_view),
    path("print_qr", views.print_qr, name="print_qr"),
    path("view_qr/<int:puzzle>", views.view_qr, name="view_qr"),
]
