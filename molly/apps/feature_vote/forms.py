from django import forms
from models import Feature
from django.utils.translation import ugettext as _

class FeatureForm(forms.ModelForm):
    user_name = forms.CharField(widget=forms.TextInput(), label=_("Your name"))
    title = forms.CharField(widget=forms.TextInput(), label=_("Feature title"))

    class Meta:
        fields = ('user_name', 'user_email', 'title', 'description')
        model = Feature
