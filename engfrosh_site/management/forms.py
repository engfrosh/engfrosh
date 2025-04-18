from django import forms
from common_models.models import Puzzle, FacilShift
from common_models.models import Calendar
from django.contrib.auth.models import User


class ShiftForm(forms.ModelForm):
    class Meta:
        model = FacilShift
        exclude = ['id']


class CalendarForm(forms.ModelForm):
    class Meta:
        model = Calendar
        exclude = ['id']


class AnnouncementForm(forms.Form):
    title = forms.CharField(label='Title', max_length=200)
    body = forms.CharField(label='Body', widget=forms.Textarea)


class DiscordNickForm(forms.Form):
    nickname = forms.CharField(label="Nickname", max_length=60)
    # 979c9f is the default discord role color
    color = forms.CharField(initial="#979c9f", widget=forms.TextInput(attrs={'type': 'color'}))

    def __init__(self, *args, nick=None, col=None, **kwargs):
        super(DiscordNickForm, self).__init__(*args, **kwargs)

        if nick is not None:
            self.fields['nickname'].value = nick
        if col is not None:
            self.fields['color'].value = col


class LockForm(forms.Form):
    duration = forms.IntegerField(label="Durations (mins)")


class HintForm(forms.Form):
    free_hints = forms.IntegerField(label="Free Hints")


class SkashForm(forms.Form):
    skash = forms.IntegerField(label="Skash")


class PuzzleForm(forms.ModelForm):
    class Meta:
        model = Puzzle
        exclude = ['id', 'secret_id', 'created_at']


class EventForm(forms.Form):
    start = forms.DateTimeField(label="Start", widget=forms.TextInput(attrs={"type": "datetime-local"}))
    end = forms.DateTimeField(label="End", widget=forms.TextInput(attrs={"type": "datetime-local"}))
    title = forms.CharField(label="Title", max_length=400)
    description = forms.CharField(label="Description", max_length=4000, widget=forms.Textarea)
    calendar = forms.MultipleChoiceField(label="Calendar", choices=[("Default", "Default")])
    color_event = forms.CharField(label="Colour", max_length=50, widget=forms.TextInput(attrs={"type": "color"}))

    def __init__(self, *args, calendar_choices=None, readonly=False, **kwargs):
        super().__init__(*args, **kwargs)
        if calendar_choices is None:
            calendar_choices = Calendar.objects.exclude(name__in=User.objects.all().values('username')).values("name")
        choices = []
        for c in calendar_choices:
            name = c['name']
            choices += [(name, name)]
        self.fields['calendar'].choices = choices
        self.fields['start'].widget = forms.TextInput()
        self.fields['end'].widget = forms.TextInput()
