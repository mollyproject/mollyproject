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
        return None
    else:
        placemarks, created = Placemarks.objects.get_or_create(query=query)
        placemarks.data = json['Placemark']
        placemarks.save()
        return json['Placemark']

def set_location(request, location, accuracy, method, placemark=None):
    if isinstance(location, list):
        location = tuple(location)

    request.preferences['location']['location'] = location
    request.preferences['location']['updated'] = datetime.now()
    request.preferences['location']['placemark'] = placemark
    request.preferences['location']['method'] = method
    request.preferences['location']['accuracy'] = accuracy

