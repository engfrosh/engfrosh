"""Admin setup for discord bot manager."""

from django.contrib import admin

from .models import ChannelTag, DiscordChannel, DiscordCommandStatus, ScavChannel, Role, DiscordOverwrite

admin.site.register([DiscordCommandStatus, Role, ScavChannel, ChannelTag, DiscordOverwrite])


@admin.action(description="Lock Channels")
def lock_discord_channels(modeladmin, request, queryset):
    """Lock Channels."""

    for obj in queryset:
        obj.lock()


@admin.action(description="Unlock Channels")
def unlock_discord_channels(modeladmin, request, queryset):
    """Unlock Channels."""

    for obj in queryset:
        obj.unlock()


class DiscordChannelAdmin(admin.ModelAdmin):
    """Admin for Discord Channels."""

    actions = [
        lock_discord_channels,
        unlock_discord_channels
    ]


admin.site.register(DiscordChannel, DiscordChannelAdmin)
