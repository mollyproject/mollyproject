from urllib import urlencode
from urllib2 import urlopen
import simplejson

from django.conf import settings
from django.contrib.gis.geos import Point, LineString
from django.utils.text import capfirst
from django.utils.translation import ugettext as _

from molly.apps.places.models import bearing_to_compass
from molly.utils.templatetags.molly_utils import humanise_distance, humanise_seconds

CYCLESTREETS_URL = 'http://www.cyclestreets.net/api/journey.json?%s'

if 'cyclestreets' not in settings.API_KEYS:
    # Cyclestreets not configured
    raise ImportError()

def generate_route(points, type):
    """
    Given 2 Points, this will return a route between them. The route consists
    of a dictionary with the following keys:
    
    * error (optional, and if set means that the object contains no route),
      which is a string describing any errors that occurred in plotting the
      route
    * total_time: An int of the number of seconds this route is estimated to
      take
    * total_distance: An int of the number of metres this route is expected to
      take
    * waypoints: A list of dictionaries, where each dictionary has 2 keys:
      'instruction', which is a human-readable description of the steps to be
      taken here, and 'location', which is a Point describing the route to be
      taken
    
    @param points: An ordered list of points to be included in this route
    @type points: [Point]
    @param type: The type of route to generate (foot, car or bike)
    @type type: str
    @return: A dictionary containing the route and metadata associated with it
    @rtype: dict
    """
    
    # Build Cyclestreets request:
    url = CYCLESTREETS_URL % urlencode({
        'key': settings.API_KEYS['cyclestreets'],
        'plan': 'balanced',
        'itinerarypoints': '|'.join('%f,%f' % (p[0], p[1]) for p in points)
    })
    
    json = simplejson.load(urlopen(url))
    
    if not json:
        return {
            'error': _('Unable to plot route')
        }
    else:
        
        summary = json['marker'][0]['@attributes']
        
        waypoints = []
        for i, waypoint in enumerate(json['marker'][1:]):
            segment = waypoint['@attributes']
            waypoints.append({
                'instruction': _('%(instruction)s at %(name)s') % {
                        'instruction': capfirst(segment['turn']),
                        'name': segment['name']
                    },
                'additional': _('%(direction)s for %(distance)s (taking approximately %(time)s)') % {
                        'direction': bearing_to_compass(int(segment['startBearing'])),
                        'distance': humanise_distance(segment['distance'], False),
                        'time': humanise_seconds(segment['time'])
                    },
                'waypoint_type': {
                        'straight on': 'straight',
                        'turn left': 'left',
                        'bear left': 'slight-left',
                        'sharp left': 'sharp-left',
                        'turn right': 'right',
                        'bear right': 'slight-right',
                        'sharp right': 'sharp-right',
                        'double-back': 'turn-around',
                    }.get(segment['turn']),
                'location': Point(*map(float, segment['points'].split(' ')[0].split(','))),
                'path': LineString(map(lambda ps: Point(*map(float, ps.split(','))),
                                       segment['points'].split(' ')))
            })
        
        return {
            'total_time': summary['time'],
            'total_distance': summary['length'],
            'waypoints': waypoints,
            'path': LineString(map(lambda ps: Point(*map(float, ps.split(','))), summary['coordinates'].split(' ')))
        }