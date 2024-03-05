"""URLs for the management pages."""

from . import views
from django.urls import path

urlpatterns = [
    path('discord/magic-link', views.get_discord_link, name="magic_links"),
    path('users/add', views.bulk_register_users),
    path('teams', views.manage_frosh_teams, name="manage_frosh_teams"),
    path('', views.manage_index, name="manage_index"),
    path('announcements', views.announcements, name="announcements"),
    # path('roles', views.manage_roles, name="manage_roles"),
    path('scavenger/puzzles', views.manage_scavenger_puzzles, name="manage_scavenger_puzzles"),
    path('scavenger/puzzles/<int:id>', views.edit_scavenger_puzzle, name="edit_scavenger_puzzle"),
    path('scavenger/approve-photos', views.approve_scavenger_puzzles, name="approve_scavenger_puzzles"),
    path('scavenger/scoreboard', views.scavenger_scoreboard, name="scavenger_scoreboard"),
    path('scavenger/monitor', views.scavenger_monitor, name="scavenger_monitor"),
    path('database/initialize', views.initialize_database, name="initialize_database"),
    path('database/scavinit', views.initialize_scav, name="initialize_scav"),
    path('trade-up/view-all', views.trade_up_viewer, name="trade_up_viewer"),
    path('users/add-to-guild', views.add_discord_user_to_guild, name="add_users_to_discord_guild"),
    path('discord/channels', views.manage_discord_channels, name="manage_discord_channels"),
    path('discord/channel-groups', views.manage_discord_channel_groups, name="manage_discord_channel_groups"),
    path('discord/nicks', views.manage_discord_nicks, name="manage_discord_nicks"),
    path('discord/nicks/<int:id>', views.manage_discord_nick, name="manage_discord_nick"),
    path('events/<int:id>', views.edit_event, name="edit_event"),
    path('lock_team/<int:id>', views.lock_team, name="lock_team"),
    path('unlock_team/<int:id>', views.unlock_team, name="unlock_team"),
    path('unregistered', views.unregistered, name="emaillisti"),
    path('facil_shifts', views.facil_shifts, name="facil_shifts"),
    path('free_hints/<int:id>', views.free_hints, name="free_hints"),
    path('mailing_list', views.mailing_list, name="mailing_list"),
    path('shift_export', views.shift_export, name="shift_export"),
    path('shift_manage/<int:id>', views.shift_manage, name="shift_manage"),
    path('reports', views.reports, name="reports")
    path('export_teams', views.export_teams, name="export_teams"),
    path('prc', views.bulk_add_prc, name="bulk_add_prc")
    path('discord_rename', views.discord_rename, name="discord_rename"),
    path('discord_create', views.discord_create, name="discord_create")
]
