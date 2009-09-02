# -*- coding: utf-8 -*-
from django.core.management.base import NoArgsCommand
from django.contrib.gis.geos import Point, LineString, LinearRing
from django.conf import settings
from mobile_portal.oxpoints.models import Entity, EntityType
from mobile_portal.core.geolocation import reverse_geocode
from mobile_portal.core.models import Config
from mobile_portal.core.utils import AnyMethodRequest
from xml.sax import saxutils, handler, make_parser
import urllib2, bz2, subprocess, popen2
from os import path

AMENITIES = {
    'bicycle_parking': ('bicycle rack', 'bicycle racks'),
    'post_box': ('post box', 'post boxes'),
    'toilets': ('public toilet', 'public toilets'),
    'recycling': ('recycling facility', 'recycling facilities'),
    'post_office': ('post office', 'post offices'),
    'pharmacy': ('pharmacy', 'pharmacies'), 
    'hospital': ('hospital', 'hospitals'), 
    'doctors': ("doctor's surgery", "doctors' surgeries"), 
    'atm': ('ATM', 'ATMs'),
    'parking': ('car park', 'car parks'),
    'pub': ('pub', 'pubs'),
    'cafe': ('café', 'cafés'),
    'restaurant': ('restaurant', 'restaurants'),
}

ENGLAND_OSM_BZ2_XML = 'http://download.geofabrik.de/osm/europe/great_britain/england.osm.bz2'
OSM_ETAG_FILENAME = path.join(settings.CACHE_DIR, 'osm_england_extract_etag')

def node_id(id):
    return "N%d" % int(id)
def way_id(id):
    return "W%d" % int(id)
        
class OxfordHandler(handler.ContentHandler):
    def startDocument(self):
        self.ids = set()
        self.tags = {}
        self.valid_node = True
        
        self.entity_types = {}
        for slug, (verbose_name, verbose_name_plural) in AMENITIES.items():
            entity_type, created = EntityType.objects.get_or_create(slug=slug)
            entity_type.verbose_name = verbose_name
            entity_type.verbose_name_plural = verbose_name_plural
            entity_type.source = 'osm'
            entity_type.id_field = 'osm_id'
            entity_type.save()
            self.entity_types[slug] = entity_type
        
        self.create_count, self.modify_count = 0,0
        self.delete_count, self.unchanged_count = 0,0
        self.ignore_count = 0
        
        self.node_locations = {}
        

        
    def startElement(self, name, attrs):
        if name == 'node':
            lat, lon = float(attrs['lat']), float(attrs['lon'])
            
            self.valid = (51.5 < lat and lat < 52.1 and -1.6 < lon and lon < -1.0)
            if not self.valid:
                return
                
            id = node_id(attrs['id'])
            
            self.node_location = lat, lon
            self.attrs = attrs
            self.id = id
            self.ids.add(id)
            self.tags = {}
            
            self.node_locations[id] = lat, lon
            
        elif name == 'tag' and self.valid:
            self.tags[attrs['k']] = attrs['v']
            
        elif name == 'way':
            self.nodes = []
            self.tags = {}
            self.valid = True
            
            id = way_id(attrs['id'])
            
            self.id = id
            self.ids.add(id)
            
        elif name == 'nd':
            self.nodes.append( node_id(attrs['ref']) )
            
    def endElement(self, name):
        if name in ('node','way') and self.valid:
            if self.tags.get('amenity') in AMENITIES:
                #print self.node_location, self.tags['amenity']
                pass
            else:
                self.ignore_count += 1
                return
            
            # Ignore ways that lay partly outside our bounding box
            if name == 'way' and not all(id in self.node_locations for id in self.nodes):
                return
                
            entity, created = Entity.objects.get_or_create(osm_id=self.id)
            
            
            if created or not entity.metadata or entity.metadata.get('attrs', {}).get('timestamp', '') < self.attrs['timestamp']:
            
                if created:
                    self.create_count += 1
                else:
                    self.modify_count += 1
                    
                if name == 'node':
                    entity.location = Point(self.node_location[1], self.node_location[0], srid=4326)
                    entity.geometry = entity.location
                elif name == 'way':
                    print self.nodes[0], self.nodes[-1]
                    cls = LinearRing if self.nodes[0] == self.nodes[-1] else LineString
                    entity.geometry = cls([self.node_locations[n] for n in self.nodes], srid=4326)
                    min_, max_ = (float('inf'), float('inf')), (float('-inf'), float('-inf'))
                    for lat, lon in [self.node_locations[n] for n in self.nodes]:
                        min_ = min(min_[0], lat), min(min_[1], lon) 
                        max_ = max(max_[0], lat), max(max_[1], lon)
                    entity.location = Point( (min_[1]+max_[1])/2 , (min_[0]+max_[0])/2 , srid=4326)
                else:
                    raise AssertionError("There should be no other types of entity we're to deal with.")
                    
                if name == 'way':
                    print "Way", entity.geometry

                entity_type = self.entity_types[self.tags['amenity']]
                try:
                    name = self.tags['name']
                except:
                    try:
                        raise Exception
                        name = ', '.join(reverse_geocode(*self.node_location)[0]['address'].split(', ')[:1])
                        name = "Near %s" % (name)
                    except:
                        name = "Near %f,%f" % (self.node_location[0], self.node_location[1])
                entity.title = name
                entity.metadata = {
                    'attrs': dict(self.attrs),
                    'tags': self.tags
                }
                entity.entity_type = entity_type
                entity.save()
                
            else:
                self.unchanged_count += 1
    
    def endDocument(self):
        for entity in Entity.objects.filter(osm_id__isnull=False):
            if not entity.osm_id in self.ids:
                entity.delete()
                self.delete_count += 1
        print "Complete"
        print "  Created:   %6d" % self.create_count
        print "  Modified:  %6d" % self.modify_count
        print "  Deleted:   %6d" % self.delete_count
        print "  Unchanged: %6d" % self.unchanged_count
        print "  Ignored:   %6d" % self.ignore_count
        

def get_osm_etag():
    try:
        return Config.objects.get(key='osm_extract_etag').value
    except Config.DoesNotExist:
        return None
        
def set_osm_etag(etag):
    config, created = Config.objects.get_or_create(key='osm_extract_etag')
    config.value = etag
    config.save()

class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list
    help = "Loads OpenStreetMap data."

    requires_model_validation = True
    
    ENGLAND_OSM_BZ2_URL = 'http://download.geofabrik.de/osm/europe/great_britain/england.osm.bz2'
    #ENGLAND_OSM_BZ2_URL = 'http://download.geofabrik.de/osm/europe/great_britain/england/shropshire.osm.bz2'

    SHELL_CMD = "wget -O- %s --quiet | bunzip2" % ENGLAND_OSM_BZ2_URL
    #    SHELL_CMD = "cat /home/alex/england.osm.bz2 | bunzip2"
    
    def handle_noargs(self, **options):
        old_etag = get_osm_etag()
        
        request = AnyMethodRequest(Command.ENGLAND_OSM_BZ2_URL, method='HEAD')
        response = urllib2.urlopen(request)
        new_etag = response.headers['ETag'][1:-1]
        
        if False and new_etag == old_etag:
            print 'OSM data not updated. Not updating.'
            return
            
        p = popen2.popen2(Command.SHELL_CMD)
        
        parser = make_parser()
        parser.setContentHandler(OxfordHandler())
        parser.parse(p[0])
        
        set_osm_etag(new_etag)
