"""URLs for the management pages."""

from . import views
from django.urls import path

urlpatterns = [
    path('discord/magic-link', views.get_discord_link),
    path('users/add', views.bulk_register_users),
    path('discord/add-to-guild', views.add_discord_user_to_guild),
    path('', views.manage_index)
]
