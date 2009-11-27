from django import forms
from django.forms.models import modelformset_factory

from models import LocationShare, UserMessage, LOCATION_ACCURACY_CHOICES

class LocationShareForm(forms.ModelForm):
    class Meta:
        model = LocationShare
        fields = ('accuracy', 'share_times', 'until')
        
class LocationShareAddForm(forms.Form):
    email = forms.EmailField()
    limit = forms.FloatField(widget=forms.TextInput(attrs={'size':4}), required=False)
    accuracy = forms.ChoiceField(choices=LOCATION_ACCURACY_CHOICES)
    
class FeedbackForm(forms.Form):
    email = forms.EmailField(label="Your e-mail address (optional)", required=False)
    body = forms.CharField(widget=forms.Textarea(), label="Feedback")

class UserMessageForm(forms.ModelForm):
    fields = ()
    
UserMessageFormSet = modelformset_factory(
    UserMessage, UserMessageForm,
    extra=0, can_delete=True)