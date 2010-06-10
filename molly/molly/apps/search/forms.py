from django import forms
from molly.conf import all_apps

# We can't pick up the list of applications when this module is imported, as
# that could lead to a circular import dependency.[0] Instead, wait until a
# SearchForm instance is requested before calling all_apps.
#
# Instead, (the outer) SearchForm creates the desired class when an instance
# is first required and transparently returns the result of calling its
# constructor.
#
# [0] e.g. Another app is being loaded which depends on molly.apps.search.
#     molly.apps.search.forms then tries to call all_apps, which would attempt
#     to load the other app again (and fail).

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
