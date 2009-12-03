from django import forms
from django.forms.models import modelformset_factory
from django.forms.util import ErrorList

from models import LocationShare, UserMessage, LOCATION_ACCURACY_CHOICES
import geolocation

class LocationShareForm(forms.ModelForm):
    class Meta:
        model = LocationShare
        fields = ('accuracy', 'share_times', 'until')
        
class LocationShareAddForm(forms.Form):
    email = forms.EmailField()
    limit = forms.FloatField(widget=forms.TextInput(attrs={'size':4}), required=False)
    accuracy = forms.ChoiceField(choices=LOCATION_ACCURACY_CHOICES)
    
class FeedbackForm(forms.Form):
    email = forms.EmailField(label="Your e-mail address (optional)", required=False)
    body = forms.CharField(widget=forms.Textarea(), label="Feedback")

class UserMessageForm(forms.ModelForm):
    fields = ()
    
UserMessageFormSet = modelformset_factory(
    UserMessage, UserMessageForm,
    extra=0, can_delete=True)

METHOD_CHOICES = (
    ('html5', 'HTML5'),
    ('gears', 'Google Gears'),
    ('manual', 'Manual update'),
    ('geocoded', 'Geocoded'),
    ('other', 'Other method'),
    ('denied', 'Update denied by user'),
    ('error', 'Error updating location'),
)

class LocationUpdateForm(forms.Form):
    latitude = forms.FloatField(required=False)
    longitude = forms.FloatField(required=False)
    accuracy = forms.FloatField(required=False)
    method = forms.ChoiceField(required=False, choices=METHOD_CHOICES)
    name = forms.CharField(required=False)
    http_method = forms.CharField()

    def clean_latitude(self):
        latitude = self.cleaned_data.get('latitude')
        if latitude is not None and not (-180 <= latitude < 180):
            raise forms.ValidationError('Must be in the range [-90, 90).')
        return latitude

    def clean_longitude(self):
        longitude = self.cleaned_data.get('longitude')
        if longitude is not None and not (-90 <= longitude < 90):
            raise forms.ValidationError('Must be in the range [-90, 90).')
        return longitude

    def clean(self):
        cleaned_data = self.cleaned_data
        
        if cleaned_data['http_method'] == 'POST':
            if cleaned_data['method'] in ('html5', 'gears', 'manual', 'geocoded', 'other'):
                for key in ('latitude', 'longitude', 'accuracy'):
                    if cleaned_data.get(key) is None:
                        self._errors[key] = ErrorList(['method requires that this field must be specified'])
                        
                if not self._errors:
                    cleaned_data['location'] = cleaned_data['latitude'], cleaned_data['longitude']
                    if not cleaned_data.get('name'):
                        cleaned_data['name'] = geolocation.reverse_geocode(
                            self.cleaned_data['latitude'],
                            self.cleaned_data['longitude'])[0][0]
                        print "LOC NAME", cleaned_data['name']
                    print "FOO NAME"
            elif cleaned_data['method'] in ('denied', 'error'):
                for key in ('latitude', 'longitude', 'accuracy'):
                    if cleaned_data.get(key) is None:
                        self._errors[key] = ErrorList(['method requires that this field must be specified'])
            else:
                self._errors['method'] = ErrorList(['This field is required'])

        else:
            for key in ('latitude', 'longitude', 'accuracy'):
                if cleaned_data.get(key) is not None:
                    self._errors[key] = ErrorList(['This field must not be specified'])
            if not cleaned_data.get('name'):
                self._errors['name'] = ErrorList(['This field is required.'])
            
        return cleaned_data