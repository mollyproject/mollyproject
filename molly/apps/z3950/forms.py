from django import forms

class SearchForm(forms.Form):
    author = forms.CharField(required=False, label="Author")
    title = forms.CharField(required=False, label="Title")
    isbn = forms.CharField(required=False, label="ISBN")
    