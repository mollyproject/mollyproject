from urllib import urlencode

from django.contrib.gis.geos import Point

from molly.maps.osm import fit_to_map
from molly.maps.models import GeneratedMap

class Map(object):
    """
    An object which represents a Map. This should be added to a context and then
    passed to @C{render_map} in your template to get the appropriate HTML.
    """
    
    def __init__(self, centre_point, points, min_points, zoom, width, height,
                 extra_points=[], paths=[]):
        """
        @param centre_point: A tuple of longitude, latitude, colour and title
                             corresponding to the "centre" of the map. This is
                             NOT necessarily the central latitude/longitude of
                             the generated image, but simply a special marker
                             which is indicated with a star.
        @type centre_point: (float, float, str, str) or None
        @param points: An (ordered) list of points to be plotted on the map.
                       These are indicated on the map with numbered markers.
                       This list consists of tuples of longitude, latitude, a
                       string indicating the colours of the markers to be
                       rendered and a title of the point to be plotted
        @type points: [(float, float, str, str)]
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
        @param extra_points: Any extra points to be plotted in the same form as
                             centre_points
        @type extra_points: list
        @param paths: A list of LineString, string tuples which contain any
                      paths to be plotted on this map. The string is a HTML
                      colour code for the path.
        @type paths: list
        """
        
        self.centre_point = centre_point
        self.extra_points = extra_points
        self.min_points = min_points
        self.paths = paths
        self.width = width
        self.height = height
        
        try:
            self.static_map_hash, \
                (self.points, self.zoom, lon_center, lat_center) = fit_to_map(
                    centre_point = centre_point,
                    extra_points = extra_points,
                    points = points,
                    paths = paths,
                    min_points = min_points,
                    zoom = zoom,
                    width = width,
                    height = height,
                )
            # Check if this uses the old format of self.points
            if len(self.points) > 0:
                # this will throw a ValueError if it can't unpack, triggering a
                # regeneration of the map
                (lon, lat, colour, title), indices = self.points[0]
        except ValueError:
            # Old style metadata, which didn't store lon_center and lat_center
            # was stored, so we need to regenerate the map
            static_map_hash, metadata = fit_to_map(
                    centre_point = centre_point,
                    extra_points = extra_points,
                    points = points,
                    paths = paths,
                    min_points = min_points,
                    zoom = zoom,
                    width = width,
                    height = height,
                )
            GeneratedMap.objects.get(hash=static_map_hash).delete()
            self.static_map_hash, \
                (self.points, self.zoom, lon_center, lat_center) = fit_to_map(
                    centre_point = centre_point,
                    extra_points = extra_points,
                    points = points,
                    paths = paths,
                    min_points = min_points,
                    zoom = zoom,
                    width = width,
                    height = height,
                )
        
        markers = [
            (str(centre_point[1]),
             str(centre_point[0]),
             centre_point[2] + '_star',
             centre_point[3].encode('ascii', 'xmlcharrefreplace'))
        ] if centre_point != None else []
        
        for point in self.extra_points:
            markers.append((str(point[1]),
                 str(point[0]),
                 point[2] + '_star',
                 point[3].encode('ascii', 'xmlcharrefreplace')))
        
        for point in self.points:
            markers.append(
                    (str(point[0][1]),
                     str(point[0][0]),
                     point[0][2] + '_' + str(point[1][0] + 1),
                     point[0][3].encode('ascii', 'xmlcharrefreplace'))
                )
        
        self.lon_centre, self.lat_centre = lon_center, lat_center
        
        self.markers = markers
    
    def simplify_for_render(self, simplify_value, simplify_model):
        return {
            'hash': simplify_value(self.static_map_hash),
            'centre_point': simplify_value(self.centre_point),
            'extra_points': simplify_value(self.extra_points),
            'points': simplify_value(self.points),
            'paths': simplify_value(self.paths),
            'width': simplify_value(self.width),
            'height': simplify_value(self.height),
            'map_centre': simplify_value(Point(self.lon_centre, self.lat_centre)),
            'zoom': simplify_value(self.zoom),
            'markers': simplify_value(self.markers),
        }


def map_from_point(point, width, height, colour='green', title='', zoom=16):
    """
    A shortcut which renders a simple map containing only one point rendered as
    a star
    """
    return Map((point[0], point[1], colour, title), [], 1, zoom, width, height)

