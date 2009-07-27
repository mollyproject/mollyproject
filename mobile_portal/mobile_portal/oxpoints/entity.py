import urllib
from xml.etree import ElementTree as ET
try:
    from mobile_portal.core.models import Feed
    def get_data(url):
        try:
            return Feed.fetch(url, fetch_period=24*3600, category="oxpoints", return_data=True, raise_if_error=True)
        except IOError:
            return MissingResource(url)
except ImportError:
    def get_data(url):
        response = urllib.urlopen(url)
        if response.code != 200:
            return MissingResource(url)
        else:
            return response.read()
    
def get_xml(url):
    data = get_data(url)
    if isinstance(data, MissingResource):
        return data
    try:
        return ET.fromstring(data)
    except:
        return NonXMLResource(url)
            

GML_NS = '{http://www.opengis.net/gml/}'
RDF_NS = '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}'
DC_NS = '{http://purl.org/dc/elements/1.1/}'
OXP_NS = '{http://ns.ox.ac.uk/namespace/oxpoints/2009/02/owl#}'

class Resource(object):
    def __init__(self, rdf):
        pass

class NonXMLResource(object):
    def __init__(self, url):
        self.url = url
    def __repr__(self):
        return '<%s "%s">' % (type(self).__name__, self.url)

class MissingResource(NonXMLResource): pass

class Entity(Resource):
    def __init__(self, rdf):
        self.title = rdf.find(DC_NS + 'title').text
        self.id = int(rdf.attrib[RDF_NS+'about'].split('/')[-1])
    def __repr__(self):
        return '<%s "%s">' % (type(self).__name__, self.title)

class Unit(Entity):
    def __init__(self, rdf):
        super(Unit, self).__init__(rdf)
        
        self.occupies = [get_resource(r) for r in get_bag(rdf.find(OXP_NS+'occupies'))]
        self.in_images = [get_resource(r) for r in get_bag(rdf.find(OXP_NS+'inImage'))]
        self.primary_place = get_resource(rdf.find(OXP_NS+'primaryPlace'))
        self.homepage = get_resource(rdf.find(OXP_NS+'hasHomepage'))

class Place(Entity):
    def __init__(self, rdf):
        super(Place, self).__init__(rdf)
        
        try:
            location = rdf.find('%s%s/%s%s/%s%s' % (OXP_NS, 'hasLocation', GML_NS, 'Point', GML_NS, 'pos')).text.split(' ')
            self.location = float(location[1]), float(location[0])
        except:
            self.location = None 

    def google_qs_part(self):
        return "%s@%f,%f" % (urllib.quote(self.title), self.location[0], self.location[1])
    google_qs_part.safe = True 

class College(Unit): pass
class Department(Unit): pass
class Library(Unit): pass
class Museum(Unit): pass
class Carpark(Place): pass
class Building(Place): pass

class LazyResource(object):
    def __init__(self, url):
        self.__url, self.__resource = url, None
        
    def __getattr__(self, name):
        if not self.__resource:
            self.__resource = get_resource_by_url(self.__url)
        return getattr(self.__resource, name)
        
    def __setattr__(self, name, value):
        if name in ('_LazyResource__resource', '_LazyResource__url'):
            self.__dict__[name] = value
            return
        if not self.__resource:
            self.__resource = get_resource_by_url(self.__url)
        return setattr(self.__resource, name, value)
        
    def __delattr__(self, name):
        if not self.__resource:
            self.__resource = get_resource_by_url(self.__url)
        return delattr(self.__resource, name)
        
    def __repr__(self):
        if not self.__resource:
            self.__resource = get_resource_by_url(self.__url)
        return self.__resource.__repr__()
    
RESOURCE_TYPES = {
    'Building': Building,
    'College': College,
    'Department': Department,
    'Library': Library,
    'Museum': Museum,
    'Carpark': Carpark,
}

def get_bag(node):
    return node.findall('%s%s/%s%s' % (RDF_NS, 'Bag', RDF_NS, 'li'))

def get_resource(node):
    return LazyResource(get_resource_url(node))

def get_resource_url(node):
    return node.attrib[RDF_NS+'resource']

def get_resource_by_url(url):
    if url in get_resource_by_url.resources:
        return get_resource_by_url.resources[url]
        
    xml = get_xml(url)
    
    if isinstance(xml, NonXMLResource):
        resource = xml
    else:
        #xml = xml.getroot()
        
        tag = xml[0].tag
        if xml[0].tag.startswith(OXP_NS):
            ptype = tag[len(OXP_NS):]
            resource = RESOURCE_TYPES[ptype](xml[0])
        else:
            resource = Resource(xml[0])
    get_resource_by_url.resources[url] = resource
    return resource
get_resource_by_url.resources = {}
