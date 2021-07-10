from django.contrib import admin

from .models import DiscordUser, MagicLink

admin.site.register([DiscordUser, MagicLink])
