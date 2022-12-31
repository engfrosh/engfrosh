from django import forms


class TicketForm(forms.Form):
    title = forms.CharField(label='Title', max_length=200)
    body = forms.CharField(label='Body', max_length=3000, widget=forms.Textarea(attrs={"rows": "5"}))


class TicketCommentForm(forms.Form):
    body = forms.CharField(label='Body', max_length=3000, widget=forms.Textarea(attrs={"rows": "5"}))


class TicketUpdateForm(forms.Form):
    status = forms.ChoiceField(label='Status', choices=[
        (1, 'IN PROGRESS'),
        (2, 'MORE INFO'),
        (3, 'CLOSED')
    ])

    def __init__(self, *args, initial=None, **kwargs):
        super(TicketUpdateForm, self).__init__(*args, **kwargs)
        if initial is not None:
            self.fields['status'].initial = initial
