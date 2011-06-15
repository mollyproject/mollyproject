from django import forms
from django.utils.translation import ugettext_lazy as _

class SearchForm(forms.Form):
    author = forms.CharField(required=False, label=_("Author"))
    title = forms.CharField(required=False, label=_("Title"))
    isbn = forms.CharField(required=False, label=_("ISBN"))
    