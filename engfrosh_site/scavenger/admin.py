"""Admin site setup for Scavenger Models."""

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


@admin.action(description="Reset selected teams' progress.")
def reset_scavenger_progress(modeladmin, request, queryset):
    """Reset selected teams scavenger progress back to the beginning."""

    for obj in queryset:
        obj.reset_progress()


class TeamAdmin(admin.ModelAdmin):
    """Admin for Scavenger Teams."""

    actions = [reset_scavenger_progress]


admin.site.register(Team, TeamAdmin)

# endregion
