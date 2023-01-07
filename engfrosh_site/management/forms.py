from django import forms


class AnnouncementForm(forms.Form):
    title = forms.CharField(label='Title', max_length=200)
    body = forms.CharField(label='Body', widget=forms.Textarea)
