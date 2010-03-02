from django import forms

METHOD_CHOICES = (
    ('phone', 'phone'),
    ('email', 'email'),
)

class GenericContactForm(forms.Form):
    query = forms.CharField()
    medium = forms.ChoiceField(choices = METHOD_CHOICES)
