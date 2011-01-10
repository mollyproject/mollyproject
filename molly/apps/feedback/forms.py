from django import forms


class FeedbackForm(forms.Form):
    email = forms.EmailField(label="Your e-mail address (optional)",
                             required=False)
    email.widget.input_type = 'email'
    body = forms.CharField(widget=forms.Textarea(), label="Feedback")
