from urllib2 import urlopen
import simplejson

from django.conf import settings
from django.contrib.gis.geos import Point

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
    
    return {'error': 'Not written yet'}