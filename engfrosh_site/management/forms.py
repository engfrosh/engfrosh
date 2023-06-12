from django import forms
from common_models.models import Puzzle
from schedule.models import Event


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


class PuzzleForm(forms.ModelForm):
    class Meta:
        model = Puzzle
        exclude = ['id', 'secret_id', 'created_at']


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['start', 'end', 'title', 'description', 'calendar', 'color_event']
        widgets = {
            "start": forms.DateTimeInput(),
            "end": forms.DateTimeInput(),
        }
