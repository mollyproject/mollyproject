from django import forms

class FeedbackForm(forms.Form):
    email = forms.EmailField(label="Your e-mail address (optional)", required=False)
    body = forms.CharField(widget=forms.Textarea(), label="Feedback")
