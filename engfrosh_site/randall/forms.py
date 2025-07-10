from common_models.models import RandallBooking
from django import forms


class RandallBookingForm(forms.ModelForm):
    class Meta:
        model = RandallBooking
        exclude = ['id', 'approved', 'user']
        widgets = {
            'start': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end': forms.DateTimeInput(attrs={'type': 'datetime-local'})
        }
