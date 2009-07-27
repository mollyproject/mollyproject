from django import forms
from django.forms.models import modelformset_factory

from models import ProfileFrontPageLink

class FrontPageLinkForm(forms.ModelForm):
    order = forms.FloatField()
    class Meta:
        model = ProfileFrontPageLink
        fields = ('order', 'displayed')
