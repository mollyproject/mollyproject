from django import forms
from django.forms.util import ErrorList

from molly.conf import applications

from utils import geocode, reverse_geocode

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
 
    def clean_latitude(self):
        latitude = self.cleaned_data.get('latitude')
        if latitude is not None and not (-180 <= latitude < 180):
            raise forms.ValidationError('Must be in the range [-180, 180).')
        return latitude

    def clean_longitude(self):
        longitude = self.cleaned_data.get('longitude')
        if longitude is not None and not (-90 <= longitude < 90):
            raise forms.ValidationError('Must be in the range [-90, 90).')
        return longitude

    def clean(self):
        cleaned_data = self.cleaned_data

        if cleaned_data['method'] in ('html5', 'gears', 'manual', 'geocoded', 'other'):
            print "CD1", cleaned_data
            if cleaned_data['method'] == 'geocoded':
                results = geocode(cleaned_data['name'])
                if len(results) > 0:
                    cleaned_data.update(results[0])
                    cleaned_data['longitude'], cleaned_data['latitude'] = cleaned_data['location']
                    cleaned_data['alternatives'] = results[1:]
                else:
                    raise forms.ValidationError("Unable to find a location that matches '%s'." % cleaned_data['name'])

            print "CD2", cleaned_data
            for key in ('latitude', 'longitude', 'accuracy'):
                if cleaned_data.get(key) is None:
                    self._errors[key] = ErrorList(['method requires that this field must be specified'])

            if not self._errors:
                cleaned_data['location'] = cleaned_data['longitude'], cleaned_data['latitude']
                if not cleaned_data.get('name'):
                    try:
                        cleaned_data['name'] = reverse_geocode(
                            self.cleaned_data['longitude'],
                            self.cleaned_data['latitude'])[0]['name']
                    except:
                        cleaned_data['name'] = None
        elif cleaned_data['method'] in ('denied', 'error'):
            for key in ('latitude', 'longitude', 'accuracy'):
                if cleaned_data.get(key) is None:
                    self._errors[key] = ErrorList(['method requires that this field must be specified'])
        else:
            self._errors['method'] = ErrorList(['This field is required'])

        return cleaned_data
