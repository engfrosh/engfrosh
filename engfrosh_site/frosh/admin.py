"""Admin setup for Frosh App."""

from django.contrib import admin

from .models import Team, FroshRole, UserDetails, UniversityProgram, DiscordBingoCards

admin.site.register([Team, FroshRole, UniversityProgram])


class UserDetailsAdmin(admin.ModelAdmin):
    """User Details Admin."""

    search_fields = ('user__username', 'name')


admin.site.register(UserDetails, UserDetailsAdmin)


class DiscordBingoCardAdmin(admin.ModelAdmin):
    """Discord Bingo Card Admin."""

    list_display = ('bingo_card', 'discord_id')
    search_fields = ('bingo_card', 'discord_id')


admin.site.register(DiscordBingoCards, DiscordBingoCardAdmin)
