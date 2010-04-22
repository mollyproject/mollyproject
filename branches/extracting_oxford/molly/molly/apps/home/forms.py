from django import forms
from django.forms.models import modelformset_factory
from django.forms.util import ErrorList

from models import UserMessage

class FeedbackForm(forms.Form):
    email = forms.EmailField(label="Your e-mail address (optional)", required=False)
    body = forms.CharField(widget=forms.Textarea(), label="Feedback")

class UserMessageForm(forms.ModelForm):
    fields = ()
    
UserMessageFormSet = modelformset_factory(
    UserMessage, UserMessageForm,
    extra=0, can_delete=True)



