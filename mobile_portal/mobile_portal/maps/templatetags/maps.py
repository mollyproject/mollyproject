from xml.etree import ElementTree as ET
import urllib, random
from django.conf import settings
from django import template
from django.contrib.gis.geos import Point
from mobile_portal.wurfl import device_parents

register = template.Library()

YAHOO_MAP_URL = 'http://local.yahooapis.com/MapsService/V1/mapImage?%s'

@register.tag(name='map')
def do_render_map(parser, token):
    try:
        args = token.split_contents()
        if len(args) == 2:
           args = template.Variable(args[1]), None
        else:
           args = map(template.Variable, args[1:])
    except:
        raise template.TemplateSyntaxError, "%r takes one or two arguments" % token.contents.split()[0]
    return MapNode(args)

GOOGLE_MAPS_BROWSERS = frozenset([
    'stupid_novarra_proxy_sub73',
    'apple_iphone_ver1',
])
GOOGLE_MAPS_INCLUDE = '<script type="text/javascript" src="http://maps.google.com/maps/api/js?sensor=false"></script>\n'

class MapNode(template.Node):
    def __init__(self, args):
	self.args = args

    def render(self, context):
        args = self.args
        print self.args
        if args[1] is None:
            arg = args[0].resolve(context)
            if isinstance(arg, Point):
                p = arg.transform(4326, clone=True)
                lat, lng = p.y, p.x
            elif isinstance(arg, basestring):
                lng, lat = map(float, arg.split(' '))
            else:
                lat, lng = map(float, arg)
        else:
            lat, lng = [float(a.resolve(context)) for a in args]

        width, height = min(600, context['device'].max_image_width), 200
        
        if device_parents[context['device'].devid] & GOOGLE_MAPS_BROWSERS:
            return self.google_map(context, lat, lng, width, height)
        else:
            return self.yahoo_map(context, lat, lng, width, height)

    def google_map(self, context, lat, lng, width, height):
        params = {
            'width': width, 'height': height,
            'lat': lat, 'lng': lng,
            'id': 'map-%08x' % random.randint(0, 16**8-1),
            'maps_include': context.get('maps_included') and '' or GOOGLE_MAPS_INCLUDE,
        }
        context['maps_included'] = True

        return """\
<div id="%(id)s" style="width:100%%; height:%(height)dpx;"> </div>        
%(maps_include)s<script type="text/javascript">
$(document).ready(function() {
    var point = new google.maps.LatLng(%(lat)f, %(lng)f);
    var options = {
        zoom: 14,
        center: point,
        mapTypeId: google.maps.MapTypeId.ROADMAP
    };
    var map = new google.maps.Map(document.getElementById("%(id)s"), options);
    var marker = new google.maps.Marker({
        position: point,
        map: map,
    });
});
</script>
""" % params

    def yahoo_map(self, context, lat, lng, width, height):
        params = {
            'appid': settings.YAHOO_API_KEY,
            'latitude': lat,
            'longitude': lng,
            'image_width':300,
            'image_height':200,
            'zoom':3,
        }
        xml = ET.parse(urllib.urlopen(YAHOO_MAP_URL % urllib.urlencode(params)))
        map_url = xml.getroot().text
        return """<img src="%s" width="300px" height="200px" alt=""/>""" % map_url
