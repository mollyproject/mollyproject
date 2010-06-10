from django import forms
from molly.conf import all_apps

class SearchForm(object):
    def __new__(cls, *args, **kwargs):
        try:
            return cls._search_form_class(*args, **kwargs)
        except AttributeError:
            cls._search_form_class = cls._get_search_form_class()
            return cls._search_form_class(*args, **kwargs)

    @classmethod
    def _get_search_form_class(cls):
        APPLICATION_CHOICES = (
            ('', 'Show all'),
        ) + tuple((app.local_name, app.title) for app in all_apps() if app.application_name)

        class SearchForm(forms.Form):
            query = forms.CharField(label='Search')
            application = forms.ChoiceField(
                label='Filter',
                widget=forms.HiddenInput(),
                choices=APPLICATION_CHOICES,
                required=False,
            )

        return SearchForm
