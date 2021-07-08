from django.contrib import admin

from .models import Question, Hint, Team, QuestionTime, Settings

admin.site.register(Hint)
admin.site.register(Team)
admin.site.register(QuestionTime)
admin.site.register(Settings)


class QuestionAdmin(admin.ModelAdmin):
    ordering = ["weight"]


admin.site.register(Question, QuestionAdmin)
