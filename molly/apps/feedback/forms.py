from django import forms
from django.utils.translation import ugettext_lazy as _

class FeedbackForm(forms.Form):
    email = forms.EmailField(label=_("Your e-mail address (optional)"),
                             required=False)
    email.widget.input_type = 'email'
    body = forms.CharField(widget=forms.Textarea(), label=_("Feedback"))
