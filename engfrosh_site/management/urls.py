"""URLs for the management pages."""

from . import views
from django.urls import path

urlpatterns = [
    path('discord/magic-link', views.get_discord_link),
    path('users/add', views.bulk_register_users),
    path('teams', views.manage_frosh_teams, name="manage_frosh_teams"),
    path('users/add-to-guild', views.add_discord_user_to_guild, name="add_users_to_discord_guild"),
    path('', views.manage_index, name="manage_index"),
    path('roles', views.manage_roles, name="manage_roles"),
    path('discord/channels', views.manage_discord_channels, name="manage_discord_channels"),
    path('discord/channel-groups', views.manage_discord_channel_groups, name="manage_discord_channel_groups")
]
