from __future__ import division
import math, random, cairo, urllib, os.path

from django.conf import settings

from mobile_portal.osm.models import OSMTile

def log2(x):
    return math.log(x)/math.log(2)

def get_tile_ref(lat_deg, lon_deg, zoom):
    lat_rad = lat_deg * math.pi / 180.0
    n = 2.0 ** zoom
    xtile = (lon_deg + 180.0) / 360.0 * n
    ytile = (1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n
    return (xtile, ytile)

def get_tile_geo(xtile, ytile, zoom):
  n = 2.0 ** zoom
  lon_deg = xtile / n * 360.0 - 180.0
  lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
  lat_deg = lat_rad * 180.0 / math.pi
  return(lat_deg, lon_deg)


def get_tile_url(xtile, ytile, zoom):
    return "http://tile.openstreetmap.org/%d/%d/%d.png" % (zoom, xtile, ytile)

def minmax(i):
    min_, max_ = float('inf'), float('-inf')
    for e in i:
        min_ = min(min_, e)
        max_ = max(max_, e)
    return min_, max_

def get_map(points, width, height, filename, zoom=None):
    lat_min, lat_max = minmax(p[0] for p in points)
    lon_min, lon_max = minmax(p[1] for p in points)
    
    if not zoom:
        size = min(width, height)
        if lat_min != lat_max:
            zoom = int(log2(360/abs(lat_min - lat_max)) + log2(size/256)-1.0)
        else:
            zoom = 16
    
    points = [(get_tile_ref(p[0], p[1], zoom), p[2], p[3]) for p in points]
    print zoom, points    
    
    lat_range, lon_range = lat_min - lat_max, lon_max - lon_min
    lat_center, lon_center = (lat_min + lat_max)/2, (lon_min + lon_max)/2
    
    tx_min, tx_max = map(int, minmax(p[0][0] for p in points))
    ty_min, ty_max = map(int, minmax(p[0][1] for p in points))
    ty_max, tx_max = ty_max+1, tx_max+1
    
    
    cx, cy = get_tile_ref(lat_center, lon_center, zoom)
    oxc = int((cx - tx_min) * 256 - width/2)
    oyc = int((cy - ty_min) * 256 - height/2)
    ox, oy = oxc, oyc-10
    
    tx_min_ = int(tx_min + ox/256)
    tx_max_ = int(tx_max + (width+ox)/256)
    ty_min_ = int(ty_min + oy/256)
    ty_max_ = int(ty_max + (height+oy)/256)
    tiles = [{'ref':(tx, ty)} for tx in range(tx_min_, tx_max_) for ty in range(ty_min_, ty_max_)]
    
    surface = cairo.ImageSurface(
        cairo.FORMAT_ARGB32,
        width, #(ty_max-ty_min)*256,
        height, #(tx_max-tx_min)*256,
    )
    context = cairo.Context(surface)
    
    for tile in tiles:
        tile_data = OSMTile.get_data(tile['ref'][0], tile['ref'][1], zoom)
        tile['surface'] = cairo.ImageSurface.create_from_png(tile_data)

        context.set_source_surface(
            tile['surface'],
            (tile['ref'][0] - tx_min) * 256 - ox,
            (tile['ref'][1] - ty_min) * 256 - oy,
        )
        
        context.rectangle(
            (tile['ref'][0] - tx_min) * 256 - ox,
            (tile['ref'][1] - ty_min) * 256 - oy,
            256, 256
        )
        
        context.fill()
    
    points.sort(key=lambda p:p[0][1])
    for (tx, ty), color, index in points:
        if index is None:
            off, fn = (10, 10), "%s-star.png" % color
        else:
            off, fn = (10, 25), "%s-%d.png" % (color, index)
        fn = os.path.join(settings.MARKER_DIR, fn)
            
        marker = cairo.ImageSurface.create_from_png(fn)
        
        off = (
            (tx - tx_min) * 256 - off[0] - ox,
            (ty - ty_min) * 256 - off[1] - oy,
        )            
        context.set_source_surface(
            marker,
            off[0], off[1]
        )
        context.rectangle(off[0], off[1], marker.get_width(), marker.get_height())
        context.fill()
        
    
    # The following is now rendered in HTML
    #context.set_source_rgb(0,0,0)
    #credit = "OpenStreetMap"
    #xbearing, ybearing, cwidth, cheight, xadvance, yadvance = (
    #    context.text_extents(credit))
    #context.select_font_face('sanf-serif', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    #context.move_to(width-cwidth-5, height-5)
    #context.show_text(credit)
           
    
    surface.write_to_png(filename)
    
    

class PointSet(set):
    def __init__(self, initial=None):
        super(PointSet, self).__init__(initial)
        self._min = (float('inf'), float('inf'))
        self._max = (float('-inf'), float('-inf'))
        self.ordered = []
        for p in initial:
            self.update(p)
        
    def add(self, p):
        super(PointSet, self).add(p)
        self.update(p)
    
    def remove(self, p):
        self.ordered.remove(p)
        super(PointSet, self).remove(p)
        if any((p[i] in (self._min[i], self._max[i])) for i in range(2)):
            self._min = (float('inf'), float('inf'))
            self._max = (float('-inf'), float('-inf'))
            for p in self:
                self._min = min(self._min[0], p[0]), min(self._min[1], p[1])
                self._max = max(self._max[0], p[0]), max(self._max[1], p[1])
    
    def update(self, p):
        self.ordered.append(p)
        self._min = min(self._min[0], p[0]), min(self._min[1], p[1])
        self._max = max(self._max[0], p[0]), max(self._max[1], p[1])
        
    def extent(self, zoom):
        tl = get_tile_ref(self._min[0], self._min[1], zoom)
        br = get_tile_ref(self._max[0], self._max[1], zoom)
        
        a = (br[0]-tl[0])*256, (tl[1]-br[1])*256
        print "Fooo" , a
        return a
        
    def contained_within(self, box, zoom):
        extent = self.extent(zoom)
        return extent[0] <= box[0] and extent[1] <= box[1]
        

def get_fitted_map(centre_point, points, min_points, zoom, width, height, filename):

    # If we haven't been given a zoom, start as close as we can
    if not zoom:
        zoom = 18

    box = width - 20, height-35
    
    new_points = []
    for i, point in enumerate(points):
        if i>1 and point == new_points[-1][0]:
            new_points[-1][1].append(i)
        else:
            new_points.append( (point, [i]) )
    
    points = [p[0] for p in new_points]
    
    if centre_point:
        points = [centre_point] + list(points)
    point_set, points = PointSet(points[:min_points+1]), points[min_points+1:]
    
    while not point_set.contained_within(box, zoom):
        zoom -= 1
        print zoom
    
    while point_set.contained_within(box, zoom):
        if not points:
            break
        new_point, points = points[0], points[1:]
        point_set.add(new_point)
    else:
        point_set.remove(new_point)
    
    used_points = point_set.ordered[1:]
    
    if centre_point:
        points = [(centre_point[0], centre_point[1], centre_point[2], None)]
    else:
        points = []
    
    for i, point in enumerate(used_points):
        points.append(
            (point[0], point[1], point[2], i+1)
        )
        
    print "Points", len(points), points
    
    print "Extent", point_set.extent(zoom)
    get_map(points, width, height, filename, zoom)
    
    if centre_point:
        new_points = new_points[:len(point_set)-1]
    else:
        new_points = new_points[:len(point_set)]
    return new_points, zoom
    
    
if __name__ == '__main__':
    RED, GREEN, BLUE = (1, 0, 0), (0, 0.5, 0), (0.25, 0.25, 1)
    get_map(
        [
            (51.760283, -1.259941, 'blue', None),
            (51.760565, -1.259021, 'red', 1),
            (51.760009, -1.260275, 'green', 2),
            (51.760294, -1.258813, 'red', 3),
            (51.759805, -1.261170, 'green', 4),
            (51.759810, -1.261359, 'red', 5),
            (51.759662, -1.261110, 'green', 6),
            (51.759520, -1.260638, 'red', 7),
            (51.759247, -1.259904, 'green', 8),
            (51.759173, -1.259880, 'red', 9),
        ], 300, 200, 'foo.png')
        
        
