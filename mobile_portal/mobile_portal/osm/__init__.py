from __future__ import division
import math, random, cairo, urllib

def log2(x):
    return math.log(x)/math.log(2)

def get_tile_ref(lat_deg, lon_deg, zoom):
    lat_rad = lat_deg * math.pi / 180.0
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return(xtile, ytile)

def get_tile_geo(xtile, ytile, zoom):
  n = 2.0 ** zoom
  lon_deg = xtile / n * 360.0 - 180.0
  lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
  lat_deg = lat_rad * 180.0 / math.pi
  return(lat_deg, lon_deg)


def get_tile_url(xtile, ytile, zoom):
    return "http://tile.openstreetmap.org/%d/%d/%d.png" % (zoom, xtile, ytile)

def get_map(lat_min, lon_min, lat_max, lon_max, width, height):
    size = max(width, height)
    zoom = int(log2(360/abs(lat_min - lat_max)) + log2(size/256))
    
    lat_min, lat_max = max(lat_min, lat_max), min(lat_min, lat_max)
    lon_min, lon_max = min(lon_min, lon_max), max(lon_min, lon_max)
    lat_range, lon_range = lat_min - lat_max, lon_max - lon_min
#    if lat_range > lon_range:
        
    
    tl = get_tile_ref(lat_min, lon_min, zoom)
    br = get_tile_ref(lat_max, lon_max, zoom)

    print tl, br    
    
    tiles = [{
        'ref': (x,y),
        'tl': get_tile_geo(x, y, zoom),
        'br': get_tile_geo(x+1, y+1, zoom),
        'url': get_tile_url(x, y, zoom),
    } for x in range(tl[0], br[0]+1) for y in range(tl[1], br[1]+1)]
    
    print lat_min, lon_min, lat_max, lon_max
    
    #print tiles
    
    tlx, tly = min(t['tl'][0] for t in tiles), min(t['tl'][1] for t in tiles)
    brx, bry = max(t['br'][0] for t in tiles), min(t['br'][1] for t in tiles)
    
    
    
    x_range, y_range = brx - tlx, bry - tly

    #print size, zoom, tl, br

    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    context = cairo.Context(surface)
    
    for tile in tiles:
        tile_data = urllib.urlopen(tile['url'])
        tile['surface'] = cairo.ImageSurface.create_from_png(tile_data)
        tile['surface'].write_to_png('%d-%d.png' % (tile['ref'][1], tile['ref'][0]))
        
        ox = (tile['ref'][0] - tl[0]) * 256 
        oy = (tile['ref'][1] - tl[1]) * 256
        
        print tile['ref'], tl
        print ox, oy
        
        context.set_source_surface(
            tile['surface'],
            ox,
            oy,
        )
            
        context.rectangle(
            -ox,
            -oy,
            256, 256)
        
        context.fill()
    
    surface.write_to_png('foo.png')
        
    
def get_map(points, width, height):
    min_, max_ = (float('inf'), float('inf')), (float('-inf'), float('-inf'))
    for p in points:
        min_ = min(min_[0], p['latitude']), min(min_[1], p['longitude'])
        max_ = max(max_[0], p['latitude']), max(max_[1], p['longitude'])
    ctr_ = (max_[0] + min_[0])/2, (max_[1] + min_[1])/2
    rng_ = (max_[0] - min_[0]), (max_[1] - min_[1])

    size = max(width, height)
    n = max(rng_)    
    
    zoom = int(log2(360/abs(n)) + log2(size/256))
    print min_, max_, zoom

    tl = get_tile_ref(max_[0], min_[1], zoom)
    br = get_tile_ref(min_[0], max_[1], zoom)

    tiles = [{
        'ref': (x,y),
        'tl': get_tile_geo(x, y, zoom),
        'br': get_tile_geo(x+1, y+1, zoom),
        'url': get_tile_url(x, y, zoom),
    } for x in range(tl[0], br[0]+1) for y in range(tl[1], br[1]+1)]
    
    tw = (br[0]-tl[0]+1), (br[1]-tl[1]+1)

    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    context = cairo.Context(surface)
    
    offset = (
        (tiles[0]['tl'][0]-ctr_[0])/(tiles[0]['tl'][0]-tiles[0]['br'][0]),    
        (tiles[0]['br'][1]-ctr_[1])/(tiles[0]['tl'][1]-tiles[1]['br'][1])    
    )
    
    print "Offset: ", offset
    
        
    for tile in tiles:
        tile_data = urllib.urlopen(tile['url'])
        tile['surface'] = cairo.ImageSurface.create_from_png(tile_data)
        tile['surface'].write_to_png('%d-%d.png' % (tile['ref'][1], tile['ref'][0]))
        
        ox = int((tile['ref'][0] - tl[0] - offset[0]) * 256)
        oy = int((tile['ref'][1] - tl[1] - offset[1]) * 256)
        
        print tile['ref'], tl
        print ox, oy
        
        context.set_source_surface(
            tile['surface'],
            ox,
            oy,
        )
            
        context.rectangle(
            ox,
            oy,
            256, 256)
        
        context.fill()

    tlc, brc = tiles[0]['tl'], tiles[-1]['br']
        
    context.set_line_width(2)    
    for p in points:
        px = (p['longitude'] - tlc[1]) / (brc[1]-tlc[1]) * (tw[1] - offset[0]) * 256
        py = 256-((p['latitude'] - tlc[0]) / (brc[0]-tlc[0]) - offset[0]/tw[0]) * height
        #px, py = 128, 128
        py=128
        print (p['latitude'] - tlc[0]) / (brc[0]-tlc[0])  * tw[0] * 256 - offset[0] * 256
        print
        print p['latitude'], tlc[0], brc[0], tw[0], offset[0], (p['latitude'] - tlc[0]) / (brc[0]-tlc[0])
        print p['longitude'], tlc[1], brc[1], tw[1], offset[1], (p['longitude'] - tlc[1]) / (brc[1]-tlc[1])
        print
        print "P", px, py
        
        
        context.set_source_rgb(*p['color'])
        context.arc(px, py, 4, 0, math.pi*2)
        context.stroke()
    
    surface.write_to_png('foo.png')    
    print tl, br
