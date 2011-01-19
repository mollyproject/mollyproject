from urllib import urlencode

from molly.maps.osm.utils import fit_to_map
from molly.maps.models import GeneratedMap

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
        
        try:
            self.static_map_hash, \
                (self.points, self.zoom, lon_center, lat_center) = fit_to_map(
                    centre_point = centre_point,
                    points = points,
                    min_points = min_points,
                    zoom = zoom,
                    width = width,
                    height = height,
                )
        except ValueError:
            print "Value Error!"
            # Old style metadata, which didn't store lon_center and lat_center
            # was stored, so we need to regenerate the map
            static_map_hash, metadata = fit_to_map(
                    centre_point = centre_point,
                    points = points,
                    min_points = min_points,
                    zoom = zoom,
                    width = width,
                    height = height,
                )
            print metadata
            print static_map_hash
            GeneratedMap.objects.get(hash=static_map_hash).delete()
            self.static_map_hash, (self.points, self.zoom, lon_center, lat_center) = fit_to_map(
                    centre_point = centre_point,
                    points = points,
                    min_points = min_points,
                    zoom = zoom,
                    width = width,
                    height = height,
                )
            print self.static_map_hash
            print (self.points, self.zoom, lon_center, lat_center)
        
        markers = [
            (str(centre_point[1]), str(centre_point[0]),
             centre_point[2] + '-star'),
        ]
        
        for point in self.points:
            markers.append(
                    (str(point[0][1]), str(point[0][0]),
                     point[0][2] + '-' + str(point[1][0] + 1))
                )
        
        self.slippy_map_parameters = urlencode({
            'lon': lon_center,
            'lat': lat_center,
            'zoom': self.zoom,
            'markers': '|'.join(map(','.join, markers))
        })

def map_from_point(point, width, height, colour='green', zoom=16):
    """
    A shortcut which renders a simple map containing only one point rendered as
    a star
    """
    return Map((point[0], point[1], colour), [], 1, zoom, width, height)