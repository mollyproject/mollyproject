from django import forms

APPLICATION_CHOICES = (
    ('', 'Show all'),
    ('maps', 'maps'),
    ('podcasts', 'podcasts'),
    ('rss', 'news'),
    ('webcams', 'webcams'),
)

class GoogleSearchForm(forms.Form):
    query = forms.CharField(label='Search')
    application = forms.ChoiceField(
        label='Filter',
        widget=forms.HiddenInput(),
        choices=APPLICATION_CHOICES,
        required=False,
    )