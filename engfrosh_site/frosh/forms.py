from django import forms


class CharterForm(forms.Form):
    file = forms.FileField()
