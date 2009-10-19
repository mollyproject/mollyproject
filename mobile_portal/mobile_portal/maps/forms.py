from django import forms

class BusstopSearchForm(forms.Form):
    id = forms.CharField(required=True, label='Search')