from datetime import datetime, timedelta
import math
from operator import itemgetter
import logging
import hashlib

try:
    import cPickle as pickle
except ImportError:
    import pickle

from molly.maps import Map
from molly.utils import haversine
from molly.routing.models import CachedRoute

logger = logging.getLogger(__name__)

ENGINES = dict()

try:
    from molly.routing.providers.cloudmade import generate_route as cloudmade
except ImportError:
    logger.info('Failed to import Cloudmade routing engine')
else:
    ENGINES['foot'] = cloudmade
    ENGINES['bicycle'] = cloudmade
    ENGINES['car'] = cloudmade

try:
    from molly.routing.providers.cyclestreets import generate_route as cyclestreets
except ImportError:
    logger.info('Failed to import Cyclestreets routing engine')
else:
    ENGINES['bicycle'] = cyclestreets

ALLOWED_ROUTING_TYPES = ENGINES.keys()

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
    * path: Representing the LineString this route follows
    
    @param points: An ordered list of points to be included in this route
    @type points: [Point]
    @param type: The type of route to generate (foot, car or bike)
    @type type: str
    @return: A dictionary containing the route and metadata associated with it
    @rtype: dict
    """
    
    generate_route = ENGINES.get(type)
    
    if generate_route is None:
        return {
            'error': 'No provider for %s configured' % type
        }
    else:
        
        cache_hash = hashlib.sha224(pickle.dumps((points, type))).hexdigest()
        
        try:
            
            cached_route = CachedRoute.objects.get(hash=cache_hash)
            
            logger.debug('Found cached route: %s', cached_route.hash)
            
            if datetime.now() < cached_route.expires:
                route = cached_route.cache
            else:
                
                logger.debug('Cached route has expired, regenerating')
                cached_route.delete()
                raise CachedRoute.DoesNotExist()
        
        except CachedRoute.DoesNotExist:
            
            route = generate_route(points, type)
            if 'waypoints' in route:
                for waypoint in route['waypoints']:
                    # Lazily generate the map
                    waypoint['map'] = Map(centre_point=None,
                                          points=[],
                                          min_points=0,
                                          zoom=None,
                                          width=320,
                                          height=240,
                                          extra_points=[
                                            (waypoint['path'][0][0], waypoint['path'][0][1], 'green', ''),
                                            (waypoint['path'][-1][0], waypoint['path'][-1][1], 'red', ''),
                                          ],
                                          paths=[(waypoint['path'], '#3c3c3c')])
            
            cached_route = CachedRoute.objects.create(
                hash=cache_hash, expires=datetime.now()+timedelta(weeks=1))
            
            cached_route.cache = route
            cached_route.save()
            
        return route


def optimise_points(points):
    """
    This algorithm takes some points and then tries to figure out the shortest
    route between them.
    
    It uses "as the crow flies" distance, which may not necessarily be the best.
    
    Points should be a list of tuples, where the first element is the object
    and the second element is the location of that object (first element is
    ignored by this algorithm, but is useful for you to correlate the resulting
    order with your original).
    
    This assumes that the first point is always the starting point of the user
    """
    
    if len(points) > 10:
        raise NotImplementedError()
    
    distances = {}
    
    for e, x in points:
        for e, y in points:
            distances[(x,y)] = haversine(x, y)
    
    def tsp_recurse(current, remaining):
        weights = []
        for point in remaining:
            path = [point[0]]
            weight = distances[(current, point[1])]
            
            next = set(remaining)
            next.remove(point)
            if next:
                path_r, weight_r = tsp_recurse(point[1], next)
                weight += weight_r
                path += path_r
            
            weights.append((path, weight))
        
        return min(weights, key=itemgetter(1))
    
    path, weight = tsp_recurse(points[0][1], set(points[1:]))
    return [points[0][0]] + path

