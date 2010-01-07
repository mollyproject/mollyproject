from django import forms

class PreferencesForm(forms.Form):
    old_pin = forms.RegexField(r'[0-9a-zA-Z]{4,}',
        label='Old PIN',
        required=False,
        widget=forms.PasswordInput())
    new_pin_a = forms.RegexField(r'[0-9a-zA-Z]{4,}',
        label='New PIN',
        required=False,
        widget=forms.PasswordInput())
    new_pin_b = forms.RegexField(r'[0-9a-zA-Z]{4,}',
        label='Repeat PIN',
        required=False,
        widget=forms.PasswordInput())

    timeout_period = forms.IntegerField(
        min_value=5,
        max_value=720)