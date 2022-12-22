"""URLs for the management pages."""

from . import views
from django.urls import path

urlpatterns = [
    path('check-in/<int:id>', views.check_in_view),
    path('', views.check_in_index),
]
