from django.contrib import admin

from .models import DiscordUser, MagicLink

admin.site.register([MagicLink])


class DiscordUserAdmin(admin.ModelAdmin):
    """Admin for Discord Users."""

    list_display = ('discord_username', 'user')
    search_fields = ('discord_username', 'user__username')


admin.site.register(DiscordUser, DiscordUserAdmin)
