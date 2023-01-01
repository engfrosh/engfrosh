from django import forms


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
