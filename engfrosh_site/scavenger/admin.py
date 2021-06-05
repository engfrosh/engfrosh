from django.contrib import admin

from .models import Question, QuestionOrder, Hint, Team, QuestionTime

admin.site.register(Question)
admin.site.register(QuestionOrder)
admin.site.register(Hint)
admin.site.register(Team)
admin.site.register(QuestionTime)
