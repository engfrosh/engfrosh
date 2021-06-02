from django.contrib import admin

from .models import DiscordCommandStatus, ScavChannel

admin.site.register(DiscordCommandStatus)
admin.site.register(ScavChannel)
