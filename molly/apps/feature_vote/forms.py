from django import forms
from models import Feature


class FeatureForm(forms.ModelForm):
    user_name = forms.CharField(widget=forms.TextInput(), label="Your name")
    title = forms.CharField(widget=forms.TextInput(), label="Feature title")

    class Meta:
        fields = ('user_name', 'user_email', 'title', 'description')
        model = Feature
