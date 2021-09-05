"""Admin setup for Frosh App."""

from django.contrib import admin

from .models import Team, FroshRole, UserDetails, UniversityProgram

admin.site.register([Team, FroshRole, UniversityProgram])


class UserDetailsAdmin(admin.ModelAdmin):
    """User Details Admin."""

    search_fields = ('user', 'name')


admin.site.register(UserDetails, UserDetailsAdmin)
