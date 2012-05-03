import urllib
import urllib2
import logging
import simplejson
import warnings

from django.conf import settings
from django.contrib.gis.gdal.datasource import OGRException
from django.contrib.gis.geos import Point

from molly.geolocation.providers import BaseGeolocationProvider

logger = logging.getLogger(__name__)


class CloudmadeGeolocationProvider(BaseGeolocationProvider):
    """
    CloudMade GeoLocation provider for geocoding and reverse geocoding,
    based on version 2 of the API
    """


    REVERSE_GEOCODE_URL = 'http://geocoding.cloudmade.com/%(api_key)s/geocoding/v2/find.js?object_type=%(type)s&around=%(lat)f,%(lon)f'
    GEOCODE_URL = 'http://geocoding.cloudmade.com/%(api_key)s/geocoding/v2/find.js?query=%(query)s&around=%(around)s&distance=%(distance)s&object_type=%(object_type)s'
    GEOCODE_URL_SIMPLE = 'http://geocoding.cloudmade.com/%(api_key)s/geocoding/v2/find.js?query=%(query)s&around=&object_type=%(object_type)s'

    def __init__(self, search_locality=None, search_around=None,
            search_distance=None, get_area=True):
        """
        CloudMade GeoLocation Provider
        DeprecationWarning: search_locality is not used anymore, due to changes in the API
        * search_around (optional): tuple (latitude, longitude) being the center of the area to make the search on
        * search_distance (optional): maximum distance in meters to make the search on
        * get_area (optional): get the name of the area around each result (e.g. "Walton Street, Jericho")
        """
        if search_locality:
            warnings.warn('search_locality is not used anymore, due to changes in the API, search_around and search_distance will provide better results.',
                    DeprecationWarning)
        self.search_around = search_around
        self.search_distance = search_distance
        self.get_area = get_area

    def reverse_geocode(self, lon, lat):

        params = {
            'api_key': settings.API_KEYS['cloudmade'],
            'lon': lon,
            'lat': lat,
            'type': 'road',
        }

        try:
            request_url = self.REVERSE_GEOCODE_URL % params
            response = urllib2.urlopen(request_url)
            logger.debug("Reverse geocode request: %s" % request_url)
            if response.code != 200:
                logger.error("Request to %s returned response code %d" % (request_url, response.code))
                return []
            json = simplejson.loads(response.read().replace('&apos;', "'"), 'utf8')
        except urllib2.HTTPError, e:
            logger.error("Cloudmade returned a non-OK response code %d", e.code)
            return []
        except urllib2.URLError, e:
            logger.error("Encountered an error reaching Cloudmade: %s", str(e))
            return []

        if not json:
            return []
        else:
            name = json['features'][0]['properties'].get('name')
            if self.get_area:
                try:
                    params['type'] = 'area'
                    data = simplejson.load(urllib2.urlopen(self.REVERSE_GEOCODE_URL % params))
                    logger.debug("Reverse geocode request: %s" % (self.REVERSE_GEOCODE_URL % params))
                    name = '%s, %s' % (name, data['features'][0]['properties']['name'])
                except Exception:
                    pass
            return [{
                'name': json['features'][0]['properties'].get('name'),
                'location': (lon, lat),
                'accuracy': 100,
            }]

    def geocode(self, query):
        """
        Geocode from a query (query being free-text), "around" and "distance"
        parameters can be specified to limit search results to an area.
        Uses version 2 of Cloudmade's Geocoding API.
        """

        if not query:
            return []

        query = query.strip()
        if query.split(' ')[0][0].isdigit():
            query = '+'.join(query.split(' ')[1:])

        params = {
            'api_key': settings.API_KEYS['cloudmade'],
            'query': urllib.quote_plus(query),
            'object_type': 'road',
        }

        if self.search_around and self.search_distance:
            params['around'] = '{0},{1}'.format(self.search_around[1],
                    self.search_around[0])
            params['distance'] = self.search_distance

        try:
            if self.search_around and self.search_distance:
                request_url = self.GEOCODE_URL % params
            else:
                request_url = self.GEOCODE_URL_SIMPLE % params
            response = urllib2.urlopen(request_url)
            logger.debug("Geocode request: %s" % request_url)
            if response.code != 200:
                logger.error("Request to %s returned response code %d"
                        % (request_url, response.code))
                return []
            json = simplejson.loads(response.read().replace('&apos;', "'"),
                    'utf8')
        except urllib2.HTTPError, e:
            logger.error("Cloudmade returned a non-OK response code %d", e.code)
            return []
        except urllib2.URLError, e:
            logger.error("Encountered an error reaching Cloudmade: %s", str(e))
            return []

        if not json:
            return []

        results = []

        features = sorted(json['features'], key=lambda f:
                len(f['properties'].get('name', 'x' * 1000)))

        for i, feature in enumerate(features):
            try:
                # Cloudmade returns a lat-long (and we use long-lats internally)
                bounds_a, bounds_b = [Point(p[1], p[0]) for p in feature['bounds']]
            except OGRException:
                # The point wasn't transformable into the co-ordinate
                # scheme desired - it's probably a long way away.
                continue

            centroid = tuple(feature['centroid']['coordinates'])
            centroid = centroid[1], centroid[0]
            accuracy = bounds_a.distance(bounds_b) / 1.414

            try:
                name = feature['properties']['name']

                if self.get_area:
                    try:
                        if i > 0:
                            raise ValueError
                        params.update({
                            'type': 'area',
                            'lat': centroid[1],
                            'lon': centroid[0],
                        })
                        # TODO this should use the "cache" instead of doing a call
                        data = simplejson.load(urllib2.urlopen(self.REVERSE_GEOCODE_URL % params))
                        logger.debug("Reverse geocode request: %s" % (self.REVERSE_GEOCODE_URL % params))
                        if name != data['features'][0]['properties']['name']:
                            name = '%s, %s' % (name, data['features'][0]['properties']['name'])
                    except Exception:
                        pass

                results.append({
                    'name': name,
                    'location': centroid,
                    'accuracy': accuracy,
                })

            except KeyError:
                results += self.reverse_geocode(*centroid)

        return results
