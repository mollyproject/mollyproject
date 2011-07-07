ENGINES = dict()

import logging
logger = logging.getLogger(__name__)

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
            'error': 'No provider configured'
        }
    else:
        return generate_route(points, type)