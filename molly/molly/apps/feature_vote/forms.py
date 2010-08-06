from django import forms

from models import Feature

class FeatureForm(forms.ModelForm):
    user_name = forms.CharField(widget=forms.TextInput())
    title = forms.CharField(widget=forms.TextInput())

    class Meta:
        fields = ('user_name', 'user_email', 'title', 'description')
        model = Feature
