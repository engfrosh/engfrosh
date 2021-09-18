from django.contrib import admin

from .models import DiscordUser, MagicLink


class DiscordUserAdmin(admin.ModelAdmin):
    """Admin for Discord Users."""

    list_display = ('discord_username', 'user')
    search_fields = ('discord_username', 'user__username')


admin.site.register(DiscordUser, DiscordUserAdmin)


class MagicLinkAdmin(admin.ModelAdmin):
    """Admin for Magic Links."""

    list_display = ('user', 'expiry', 'delete_immediately')

admin.site.register(MagicLink, MagicLinkAdmin)