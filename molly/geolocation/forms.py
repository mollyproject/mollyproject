# -*- coding: utf-8 -*-
import re

from django import forms
from django.forms.util import ErrorList
from django.utils.translation import ugettext_lazy as _

from molly.conf import applications
from molly.geolocation import geocode, reverse_geocode

METHOD_CHOICES = (
    ('html5', 'HTML5'),
    ('html5request', 'HTML5 (triggered by the user)'),
    ('gears', 'Google Gears'),
    ('manual', 'Manual update'),
    ('geocoded', 'Geocoded'),
    ('other', 'Other method'),
    ('denied', 'Update denied by user'),
    ('error', 'Error updating location'),
    ('favourite', 'Manually selected from favourite location list'),
)

# From http://en.wikipedia.org/wiki/Postcodes_in_the_United_Kingdom
POSTCODE_RE = r'(((A[BL]|B[ABDHLNRSTX]?|C[ABFHMORTVW]|D[ADEGHLNTY]|E[HNX]?|' + \
              r'F[KY]|G[LUY]?|H[ADGPRSUX]|I[GMPV]|JE|K[ATWY]|L[ADELNSU]?|M[' + \
              r'EKL]?|N[EGNPRW]?|O[LX]|P[AEHLOR]|R[GHM]|S[AEGKLMNOPRSTY]?|T' + \
              r'[ADFNQRSW]|UB|W[ADFNRSV]|YO|ZE)[1-9]?[0-9]|((E|N|NW|SE|SW|W' + \
              r')1|EC[1-4]|WC[12])[A-HJKMNPR-Y]|(SW|W)([2-9]|[1-9][0-9])|EC' + \
              r'[1-9][0-9]) [0-9][ABD-HJLNP-UW-Z]{2})'

class LocationUpdateForm(forms.Form):
    latitude = forms.FloatField(required=False)
    longitude = forms.FloatField(required=False)
    accuracy = forms.FloatField(required=False)
    method = forms.ChoiceField(required=False, choices=METHOD_CHOICES)
    name = forms.CharField(required=False)
 
    def clean_latitude(self):
        latitude = self.cleaned_data.get('latitude')
        if latitude is not None and not (-180 <= latitude < 180):
            raise forms.ValidationError(_('Must be in the range [-180, 180).'))
        return latitude

    def clean_longitude(self):
        longitude = self.cleaned_data.get('longitude')
        if longitude is not None and not (-90 <= longitude < 90):
            raise forms.ValidationError(_('Must be in the range [-90, 90).'))
        return longitude

    def clean(self):
        cleaned_data = self.cleaned_data

        if cleaned_data['method'] in ('html5', 'html5request', 'gears','manual', 'geocoded', 'other', 'favourite'):
            if cleaned_data['method'] == 'geocoded':
                
                if not cleaned_data['name'].strip():
                    raise forms.ValidationError(_("You must enter a location"))
                
                results = geocode(cleaned_data['name'])
                if len(results) > 0:
                    cleaned_data.update(results[0])
                    cleaned_data['longitude'], cleaned_data['latitude'] = cleaned_data['location']
                    # Ignore alternatives for postcodes
                    if not re.match(POSTCODE_RE, cleaned_data['name'].upper()):
                        cleaned_data['alternatives'] = results[1:]
                    else:
                        cleaned_data['alternatives'] = []
                else:
                    raise forms.ValidationError(_("Unable to find a location that matches '%s'.") % cleaned_data['name'])

            for key in ('latitude', 'longitude', 'accuracy'):
                if cleaned_data.get(key) is None:
                    self._errors[key] = ErrorList(['method requires that ' + key + ' must be specified'])

            if not self._errors:
                cleaned_data['location'] = cleaned_data['longitude'], cleaned_data['latitude']
                if not cleaned_data.get('name'):
                    try:
                        cleaned_data['name'] = reverse_geocode(
                            self.cleaned_data['longitude'],
                            self.cleaned_data['latitude'])[0]['name']
                    except:
                        cleaned_data['name'] = u"↝ %f, %f" % (self.cleaned_data['longitude'], self.cleaned_data['latitude'])
        elif cleaned_data['method'] in ('denied', 'error'):
            for key in ('latitude', 'longitude', 'accuracy'):
                if cleaned_data.get(key) is None:
                    self._errors[key] = ErrorList(['method requires that ' + key + ' must be specified'])
        else:
            self._errors['method'] = ErrorList(['method is required'])

        return cleaned_data
