from django import forms


class CheckInForm(forms.Form):
    name = forms.CharField(label="Name", max_length=100)
