import urllib, logging

import simplejson

from django.conf import settings

from molly.geolocation.providers import BaseGeolocationProvider

logger = logging.getLogger('molly.contrib.generic.cloudmade')

class CloudmadeGeolocationProvider(BaseGeolocationProvider):
    REVERSE_GEOCODE_URL = 'http://geocoding.cloudmade.com/%(api_key)s/geocoding/closest/road/%(lat)f,%(lon)f.js'
    GEOCODE_URL = 'http://geocoding.cloudmade.com/%(api_key)s/geocoding/find/%(query)s.js'
    
    search_locality = None
    restrict_to = None
    
    @classmethod
    def reverse_geocode(cls, lon, lat):
    
        params = {
            'api_key': settings.API_KEYS['cloudmade'],
            'lon': lon,
            'lat': lat,
        }
    
        data = urllib.urlopen(cls.REVERSE_GEOCODE_URL % params)
        
        json = simplejson.load(data.replace('&apos;', "'"), 'utf8')
        if not json:
            placemark = None
        else:
            placemark = {
                'name': json['features'][0]['properties']['name'],
                'location': (lon, lat),
                'accuracy': 100,
            }
    
        return [placemark]
        
    @classmethod
    def geocode(cls, query):
    
        if cls.search_locality and not (', ' in query or ' near ' in query):
            query += ', %s' & cls.search_locality
            
        query = query.strip()
        if query.split(' ')[0][0].isdigit():
            query = ' '.join(query.split(' ')[1:])
        
        params = {
            'api_key': settings.API_KEYS['cloudmade'],
            'query': urllib.quote_plus(query),
        }
        
        try:
            request_url = cls.GEOCODE_URL % params
            response = urllib.urlopen(request_url)
            if response.code != 200:
                logger.error("Request to %s returned response code %d" % (request_url, response.code))
                return []
            json = simplejson.loads(response.read().replace('&apos;', "'"), 'utf8')
        except Exception,e:
            raise
            return []
        
        if not json:
            return []
    
        restricted_results = []
        if cls.restrict_to:
            centre, distance = cls.restrict_to
            centre = Point(centre, srid=4326).transform(settings.SRID, clone=True)
        
            for feature in json['features']:
                try:
                    bounds_a, bounds_b = [Point(p[1], p[0], srid=4326).transform(settings.SRID, clone=True) for p in feature['bounds']]
                except OGRException:
                    # The point wasn't transformable into the co-ordinate
                    # scheme desired - it's probably a long way away.
                    continue
                    
                centroid = tuple(feature['centroid']['coordinates'])
                accuracy = bounds_a.distance(bounds_b) / 1.414
                try:
                    results.append({
                        'name': feature['properties']['name'],
                        'location': centroid,
                        'accuracy': accuracy,
                    })
                except KeyError:
                    results += cls.reverse_geocode(*centroid)
                    
                centroid = Point(centroid[1], centroid[0], srid=4326).transform(27700, clone=True)
                if centroid.distance(centre_of_oxford) < distance:
                    restricted_results.append( results[-1] )
            
        results = restricted_results or results
        
        return results