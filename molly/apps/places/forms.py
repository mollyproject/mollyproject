from django import forms
from django.utils.translation import ugettext_lazy as _

YES_NO_DEFAULT = (
    ('', ''),
    ('yes', 'Yes'),
    ('no', 'No'),
)


class UpdateOSMForm(forms.Form):
    contributor_name = forms.CharField(required=False, label=_('Your name'))
    contributor_email = forms.EmailField(required=False, label=_('Your e-mail address'))
    contributor_attribute = forms.BooleanField(required=False, label=_('Include name in update'))


    name = forms.CharField(required=False)
    operator = forms.CharField(required=False)
    opening_hours = forms.CharField(required=False, label=_('Opening hours'))
    cuisine = forms.CharField(required=False, label=_('Cuisine'))

    phone = forms.CharField(required=False, label=_('Phone number'))

    food = forms.ChoiceField(required=False, label=_('Food served'), choices=YES_NO_DEFAULT)
    food__hours = forms.CharField(required=False, label=_('Hours food is served'))

    atm = forms.ChoiceField(required=False, label=_('ATM present'), choices=YES_NO_DEFAULT)

    url = forms.CharField(required=False, label=_('Website'))

    ref = forms.CharField(required=False, label=_("Reference (e.g. 'OX1 123')"))
    collection_times = forms.CharField(required=False, label=_('Collection times'))

    capacity = forms.CharField(required=False, label=_('Capacity'))

    notes = forms.CharField(required=False, widget = forms.Textarea())
