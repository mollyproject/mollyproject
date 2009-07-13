from operator import add
from datetime import datetime
import urllib, urllib2, simplejson, math
from django.conf import settings
from django.http import HttpRequest
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

def set_location(request, placemark, latitude=None, longitude=None, method='unknown'):
    if latitude is None:
        coordinates = placemark['Point']['coordinates']
        # Placemarks have these things the wrong way round 
        latitude, longitude = coordinates[1], coordinates[0]
    request.session['location'] = latitude, longitude
    request.session['location_updated'] = datetime.now()
    request.session['placemark'] = placemark
    request.session['location_method'] = method

def normalise(obj):
    if isinstance(obj, tuple):
        return obj
    if isinstance(obj, HttpRequest):
        return obj.session['location']
    if isinstance(obj, dict):
        try:
            p = obj['oxp_hasLocation']['geo_pos'].split(' ')
            return map(float, (p[1], p[0]))
        except KeyError:
            try:
                postcode = obj['vCard_adr']['vCard_postal_code']
                location = geocode(postcode)
                return location[0]['Point']['coordinates'][:2]
            except:
                return None

def latlon_to_xyz(lat, lon):
    # 0,  0 -> 1, 0, 0
    # 90, 0 -> 0, 0, 1
    # 0, 90 -> 0, 1, 0

    lat, lon = lat * math.pi/180, lon * math.pi/180   
    
    a, z = math.cos(lat), math.sin(lat)
    x, y = math.cos(lon), math.sin(lon)
    x, y = a*x, a*y
    
    return x, y, z

def dot_product(a, b):
    return sum(c*d for c,d in zip(a, b))
    
RADIUS_OF_EARTH = 6371
def distance(a, b):
    print normalise(a), normalise(b), a
    a, b = (normalise(p) for p in (a,b))
    if not (a and b): return None
    f = dot_product(*[latlon_to_xyz(*p) for p in (a,b)])
    return RADIUS_OF_EARTH * math.acos(f)
    