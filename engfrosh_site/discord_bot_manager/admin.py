"""Admin setup for discord bot manager."""

from django.contrib import admin

from .models import DiscordCommandStatus, ScavChannel, Role

admin.site.register([DiscordCommandStatus, Role, ScavChannel])
