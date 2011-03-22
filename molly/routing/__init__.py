try:
    from molly.routing.providers.cloudmade import generate_route
except ImportError:
    
    def generate_route(start, end):
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
        
        @param start: The start of the route
        @type start: Point
        @param end: The end of the route
        @type end: Point
        @return: A dictionary containing the route and metadata associated with it
        @rtype: dict
        """
        
        return {
            'error': 'No provider configured'
        }