"""Admin setup for Frosh App."""

from django.contrib import admin

from .models import Team, FroshRole, UserDetails, UniversityProgram

admin.site.register([Team, FroshRole, UserDetails, UniversityProgram])
