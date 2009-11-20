from django import forms

APPLICATION_CHOICES = (
    ('', 'Show all'),
    ('maps', 'Maps'),
    ('podcasts', 'Podcasts'),
    ('rss', 'News'),
    ('webcams', 'Webcams'),
)

class GoogleSearchForm(forms.Form):
    query = forms.CharField(label='Search')
    application = forms.ChoiceField(
        label='Filter',
        widget=forms.HiddenInput(),
        choices=APPLICATION_CHOICES,
        required=False,
    )