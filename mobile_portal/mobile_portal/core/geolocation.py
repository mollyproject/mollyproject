"""
Geospatial-related functions, including geocoding.
"""

from operator import add
from datetime import datetime
import urllib, urllib2, simplejson, math
from django.conf import settings
from django.http import HttpRequest
from django.contrib.gis.geos import Point
from models import Placemarks

GOOGLE_MAPS_GEO_URL = 'http://maps.google.com/maps/geo?%s'
def reverse_geocode(lat, lon):
    try:
        placemarks = Placemarks.recent.get(latitude=lat, longitude=lon)
        return placemarks.data
    except Placemarks.DoesNotExist:
        pass
    query_string = urllib.urlencode({
        'q': '%f,%f' % (lat, lon),
        'key': settings.GOOGLE_API_KEY,
        'output': 'json',
        'sensor': 'true',
        'oe': 'utf8',
        'gl': 'uk',
    })
    
    data = urllib2.urlopen(GOOGLE_MAPS_GEO_URL % query_string)
    json = simplejson.load(data, 'utf8')
    if json['Status']['code'] != 200:
        print json
        return []
    else:
        placemarks, created = Placemarks.objects.get_or_create(latitude=lat, longitude=lon)
        placemarks.data = json['Placemark']
        placemarks.save()
        return json['Placemark']
        
def geocode(query):
    if query:
        try:
            placemarks = Placemarks.recent.get(query=query)
            return placemarks.data
        except Placemarks.DoesNotExist:
            pass 
    query_string = urllib.urlencode({
        'q': query,
        'key': settings.GOOGLE_API_KEY,
        'output': 'json',
        'sensor': 'true',
        'oe': 'utf8',
        'gl': 'uk',
    })
    
    data = urllib2.urlopen(GOOGLE_MAPS_GEO_URL % query_string)
    json = simplejson.load(data, 'utf8')
    if json['Status']['code'] != 200:
        print json
        return None
    else:
        placemarks, created = Placemarks.objects.get_or_create(query=query)
        placemarks.data = json['Placemark']
        placemarks.save()
        return json['Placemark']

def set_location(request, location, accuracy, method, placemark=None):

    request.session['location'] = location
    request.session['location_updated'] = datetime.now()
    request.session['placemark'] = placemark
    request.session['location_method'] = method
    request.location_set = True
    request.session['location_accuracy'] = accuracy

    if request.user and request.user.is_authenticated():
        profile = request.user.get_profile()
        profile.location = Point(location, srid=4326)
        profile.location_updated = datetime.now()
        profile.location_method = method
        profile.location_accuracy = accuracy
        profile.save()
        