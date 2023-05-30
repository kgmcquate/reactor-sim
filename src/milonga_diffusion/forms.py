from django import forms
from django.forms import ValidationError
#from crispy_forms.helper import FormHelper

def validate_size(value):
    if value > 25 or value < 5:
        raise ValidationError(('Must be between 5 and 25'))

class AddForm(forms.Form):
    x_size = forms.IntegerField( 
    label = "",
    widget=forms.TextInput(
        attrs={'class': 'form-control'}
    ),
    )

    y_size = forms.IntegerField(
    label = "",
    widget=forms.TextInput(
    attrs={'class': 'form-control',}
    ),
    )



