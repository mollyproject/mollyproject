from django import forms
from django.forms.models import modelformset_factory

from models import LocationShare, LOCATION_ACCURACY_CHOICES

class LocationShareForm(forms.ModelForm):
    class Meta:
        model = LocationShare
        fields = ('accuracy', 'share_times', 'until')
        
class LocationShareAddForm(forms.Form):
    email = forms.EmailField()
    limit = forms.FloatField(widget=forms.TextInput(attrs={'size':4}), required=False)
    accuracy = forms.ChoiceField(choices=LOCATION_ACCURACY_CHOICES)
    
class ContactForm(forms.Form):
    email = forms.EmailField()
    body = forms.CharField(widget=forms.Textarea())
    