from molly.maps.osm.utils import fit_to_map

class Map:
    """
    An object which represents a Map. This should be added to a context and then
    passed to @C{render_map} in your template to get the appropriate HTML
    """
    
    def __init__(self, centre_point, points, min_points, zoom, width, height):
        """
        @param centre_point: A tuple of longitude, latitude and colour
                             corresponding to the "centre" of the map. This is
                             NOT necessarily the central latitude/longitude of
                             the generated image, but simply a special marker
                             which is indicated with a star.
        @type centre_point: (float, float, str) or None
        @param points: An (ordered) list of points to be plotted on the map.
                       These are indicated on the map with numbered markers.
                       This list consists of tuples of longitude, latitude and a
                       string indicating the colours of the markers to be
                       rendered.
        @type points: [(float, float, str)]
        @param min_points: The minimum number of points to be displayed on the
                           resulting map
        @type min_points: int
        @param zoom: A bound on the maximum zoom level to be rendered. If this
                     zoom level is too small to fit @C{min_points} points on it,
                     then the map will be zoomed out further to fit in. If this
                     is None, then this is equivalent to the smallest zoom
                     level.
        @type zoom: int
        @param width: The width of the generated map image, in pixels
        @type width: int
        @param height: The height of the generated map image, in pixels
        @type height: int
        """
        
        self.centre_point = centre_point
        self.min_points = min_points
        self.width = width
        self.height = height
        
        self.static_map_hash, (self.points, self.zoom) = fit_to_map(
            centre_point = centre_point,
            points = points,
            min_points = min_points,
            zoom = zoom,
            width = width,
            height = height,
        )

def map_from_point(point, width, height, colour='green'):
    """
    A shortcut which renders a simple map containing only one point rendered as
    a star
    """
    return Map((point[0], point[1], colour), [], 1, 18, width, height)