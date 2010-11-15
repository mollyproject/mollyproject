from django import forms
from django.forms.models import modelformset_factory

from models import UserMessage

class UserMessageForm(forms.ModelForm):
    fields = ()
    
UserMessageFormSet = modelformset_factory(
    UserMessage, UserMessageForm,
    extra=0, can_delete=True)



