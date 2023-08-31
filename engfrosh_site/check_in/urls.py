"""URLs for the management pages."""

from . import views
from django.urls import path

urlpatterns = [
    path('check-in/<int:id>', views.check_in_view),
    path('', views.check_in_index, name="check-in-index"),
    path('monitor', views.check_in_monitor),
    path('rafting/<int:id>', views.rafting),
    path('hardhat/<int:id>', views.hardhat),
    path('brightspace/<int:id>', views.brightspace),
    path('prc/<int:id>', views.prc)
]
