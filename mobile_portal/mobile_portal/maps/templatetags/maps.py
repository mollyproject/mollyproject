from xml.etree import ElementTree as ET
import urllib
from django.conf import settings
from django import template

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

class MapNode(template.Node):
    def __init__(self, args):
	self.args = args

    def render(self, context):
        args = self.args
        if args[1] is None:
            lat, lng = [float(f) for f in args[0].resolve(context)]
        else:
            lat, lng = [float(a.resolve(context)) for a in args]
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
