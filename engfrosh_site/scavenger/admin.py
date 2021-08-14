"""Admin site setup for Scavenger Models."""

import datetime
from django.contrib import admin

from .models import Question, Hint, Team, QuestionTime, Settings

admin.site.register([Hint, QuestionTime, Settings])


# region Question Admin
class QuestionAdmin(admin.ModelAdmin):
    """Admin for Scavenger Questions."""

    ordering = ["weight"]


admin.site.register(Question, QuestionAdmin)
# endregion

# region Team Admin


@admin.action(description="Reset selected teams' progress")
def reset_scavenger_progress(modeladmin, request, queryset):
    """Reset selected teams scavenger progress back to the beginning."""

    for obj in queryset:
        obj.reset_progress()


@admin.action(description="Remove lockouts and cooldowns")
def remove_lockouts_cooldowns(modeladmin, request, queryset):
    """Remove the lockouts and cooldowns for selected teams."""

    for obj in queryset:
        obj.remove_blocks()


@admin.action(description="Lockout teams for 15 minutes")
def lockout_15_minutes(modeladmin, request, queryset):
    """Lockout teams for 15 minutes."""

    for obj in queryset:
        obj.lockout(datetime.timedelta(minutes=15))


class TeamAdmin(admin.ModelAdmin):
    """Admin for Scavenger Teams."""

    actions = [
        reset_scavenger_progress,
        remove_lockouts_cooldowns,
        lockout_15_minutes
    ]


admin.site.register(Team, TeamAdmin)

# endregion
