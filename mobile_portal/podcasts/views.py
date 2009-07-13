# Create your views here.
import urllib
from xml.etree import ElementTree as ET
from mobile_portal.core.renderers import mobile_render

RSS_FEED = 'http://rss.oucs.ox.ac.uk/mpls/oxsci-audio/rss20.xml?destination=poau'
def index(request):
    xml = ET.fromstring(urllib.urlopen(RSS_FEED).read())
    items = xml.findall('.//item')
    context = {
        'items': [{'url':i.find('enclosure').attrib['url'], 'title':i.find('title').text} for i in items],
    }
    #raise Exception(items[0].getchildren())
    return mobile_render(request, context, 'podcasts/index')
