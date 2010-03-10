from django import forms

class GenericContactForm(forms.Form):
    query = forms.CharField()
