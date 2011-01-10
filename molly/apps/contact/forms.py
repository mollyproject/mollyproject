"""
Defines contact form fields
"""
from django import forms


class GenericContactForm(forms.Form):
    """ Defines Contact Form search field """
    query = forms.CharField()
