"""
Geospatial-related functions, including geocoding.
"""

from __future__ import division
from operator import add
from datetime import datetime
import urllib, urllib2, simplejson, math, re, sys
from django.conf import settings
from django.http import HttpRequest
from django.contrib.gis.geos import Point
from django.contrib.gis.gdal import OGRException
from models import Placemarks
from mobile_portal.oxpoints.models import Entity, PostCode

CLOUDMADE_REVERSE_GEOCODE_URL = 'http://geocoding.cloudmade.com/%(api_key)s/geocoding/closest/road/%(lat)f,%(lon)f.js'
CLOUDMADE_GEOCODE_URL = 'http://geocoding.cloudmade.com/%(api_key)s/geocoding/find/%(query)s.js'

def reverse_geocode(lat, lon):

    try:
        placemarks = Placemarks.recent.get(latitude=lat, longitude=lon)
        return placemarks.data
    except Placemarks.DoesNotExist:
        pass
        
    params = {
        'api_key': settings.CLOUDMADE_API_KEY,
        'lat': lat,
        'lon': lon,
    }

    data = urllib2.urlopen(CLOUDMADE_REVERSE_GEOCODE_URL % params)
    
    json = simplejson.load(data, 'utf8')
    if not json:
        placemark = None
    else:
        placemark = json['features'][0]['properties']['name'], (lat, lon), 100

    placemarks, created = Placemarks.objects.get_or_create(latitude=lat, longitude=lon)
    placemarks.data = [placemark]
    placemarks.save()
    
    return [placemark]

UNIT_CODE_RE = re.compile(r'^[a-z]{4}$')
POST_CODE_RE = re.compile(r'^[A-Z]{1,2}[0-9R][0-9A-Z]? ?[0-9][ABD-HJLNP-UW-Z]{2}$')

def geocode_unit_code(query):
    try:
        data = simplejson.load(urllib.urlopen('http://m.ox.ac.uk/oxpoints/oucs:%s.json' % query))
        location = map(float, data[0]['oxp_hasLocation']['geo_pos'].split(' '))
        
    except ValueError:
        return []
    else:
        return [ (
            data[0]['dc_title'],
            (location[1], location[0]),
            100,
        ) ]

def geocode_post_code(query):
    if not ' ' in query:
        query = '%s %s' % (query[:-3], query[-3:])
         
    try:
        post_code = PostCode.objects.get(post_code=query)
    except PostCode.DoesNotExist:
        return []
    else:
        return reverse_geocode(post_code.location[1], post_code.location[0])
            

def geocode(query):

    try:
        placemarks = Placemarks.recent.get(query=query)
        return placemarks.data
    except Placemarks.DoesNotExist:
        pass

    results = []
    
    if UNIT_CODE_RE.match(query.lower()):
        results += geocode_unit_code(query.lower())

    if POST_CODE_RE.match(query.upper()):
        results += geocode_post_code(query.upper())
        
    for entity in Entity.objects.filter(entity_type__source='oxpoints', title__iexact=query):
        results.append( (
            entity.title, (entity.location[1], entity.location[0]), 150
        ) )
        
    if results:
        return results
        
    if not (', ' in query or ' near ' in query):
        query += ', Oxford'
        
    query = query.strip()
    if query.split(' ')[0][0].isdigit():
        query = ' '.join(query.split(' ')[1:])
    
    params = {
        'api_key': settings.CLOUDMADE_API_KEY,
        'query': urllib.quote_plus(query),
    }
    
    try:
        data = urllib2.urlopen(CLOUDMADE_GEOCODE_URL % params)
        json = simplejson.load(data, 'utf8')
    except Exception,e:
        return []
    
    if not json:
        return []

    restricted_results = []
    centre_of_oxford = Point(-1.2582, 51.7522, srid=4326).transform(27700, clone=True)
    for feature in json['features']:
        try:
            bounds_a, bounds_b = [Point(p[1], p[0], srid=4326).transform(27700, clone=True) for p in feature['bounds']]
        except OGRException:
            # The point wasn't transformable into BGS - it's probably outside the UK.
            continue
            
        centroid = tuple(feature['centroid']['coordinates'])
        accuracy = bounds_a.distance(bounds_b) / 1.414
        try:
            results.append( (
                feature['properties']['name'], centroid, accuracy
            ) )
        except KeyError:
            results += reverse_geocode(*centroid)
        centroid = Point(centroid[1], centroid[0], srid=4326).transform(27700, clone=True)
        if centroid.distance(centre_of_oxford) < 2500:
            restricted_results.append( results[-1] )
        
    results = restricted_results or results
    
    placemarks, created = Placemarks.objects.get_or_create(query=query)
    placemarks.data = results
    placemarks.save()
    
    return results

def set_location(request, location, accuracy, method, placemark=None):
    if isinstance(location, list):
        location = tuple(location)

    request.preferences['location']['location'] = location
    request.preferences['location']['updated'] = datetime.now()
    request.preferences['location']['placemark'] = placemark
    request.preferences['location']['method'] = method
    request.preferences['location']['accuracy'] = accuracy

