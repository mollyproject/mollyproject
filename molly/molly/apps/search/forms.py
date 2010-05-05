from django import forms
from molly.conf import all_apps

APPLICATION_CHOICES = (
    ('', 'Show all'),
) + tuple((app.local_name, app.title) for app in all_apps())

class SearchForm(forms.Form):
    query = forms.CharField(label='Search')
    application = forms.ChoiceField(
        label='Filter',
        widget=forms.HiddenInput(),
        choices=APPLICATION_CHOICES,
        required=False,
    )
