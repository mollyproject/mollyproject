from django import forms

YES_NO_DEFAULT = (
    ('', ''),
    ('yes', 'Yes'),
    ('no', 'No'),
)


class UpdateOSMForm(forms.Form):
    contributor_name = forms.CharField(required=False, label='Your name')
    contributor_email = forms.EmailField(required=False, label='Your e-mail address')
    contributor_attribute = forms.BooleanField(required=False, label='Include name in update')


    name = forms.CharField(required=False)
    operator = forms.CharField(required=False)
    opening_hours = forms.CharField(required=False, label='Opening hours')
    cuisine = forms.CharField(required=False, label='Cuisine')

    phone = forms.CharField(required=False, label='Phone number')

    food = forms.ChoiceField(required=False, label='Food served', choices=YES_NO_DEFAULT)
    food__hours = forms.CharField(required=False, label='Hours food is served')

    atm = forms.ChoiceField(required=False, label='ATM present', choices=YES_NO_DEFAULT)

    url = forms.CharField(required=False, label='Website')

    ref = forms.CharField(required=False, label="Reference (e.g. 'OX1 123')")
    collection_times = forms.CharField(required=False, label='Collection times')

    capacity = forms.CharField(required=False, label='Capacity')

    notes = forms.CharField(required=False, widget = forms.Textarea())
