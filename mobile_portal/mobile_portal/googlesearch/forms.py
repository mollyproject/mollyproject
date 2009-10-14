from django import forms

class GoogleSearchForm(forms.Form):
    query = forms.CharField(label='Search')