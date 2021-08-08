"""Admin setup for Frosh App."""

from django.contrib import admin

from .models import Team, FroshRole

admin.site.register([Team, FroshRole])
