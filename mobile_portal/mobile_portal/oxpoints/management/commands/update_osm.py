# -*- coding: utf-8 -*-
from django.core.management.base import NoArgsCommand
from django.contrib.gis.geos import Point
from django.conf import settings
from mobile_portal.oxpoints.models import Entity, EntityType
from mobile_portal.core.geolocation import reverse_geocode

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
    'parking': ('public car park', 'public car parks'),
    'pub': ('pub', 'pubs'),
    'cafe': ('café', 'cafés'),
    'restaurant': ('restaurant', 'restaurants'),
}

ENGLAND_OSM_BZ2_XML = 'http://download.geofabrik.de/osm/europe/great_britain/england.osm.bz2'
OSM_ETAG_FILENAME = path.join(settings.CACHE_DIR, 'osm_england_extract_etag')
class OxfordHandler(handler.ContentHandler):
    def startDocument(self):
        self.node_ids = set()
        self.tags = {}
        self.valid_node = True
        
        self.entity_types = {}
        for slug, (verbose_name, verbose_name_plural) in AMENITIES.items():
            entity_type, created = EntityType.objects.get_or_create(slug=slug)
            entity_type.verbose_name = verbose_name
            entity_type.verbose_name_plural = verbose_name_plural
            entity_type.source = 'osm'
            entity_type.save()
            self.entity_types[slug] = entity_type
        
        self.create_count, self.modify_count = 0,0
        self.delete_count, self.unchanged_count = 0,0
        self.ignore_count = 0    
        
    def startElement(self, name, attrs):
        if name == 'node':
            lat, lon = float(attrs['lat']), float(attrs['lon'])
            
            self.valid_node = (51.5 < lat and lat < 52.1 and -1.6 < lon and lon < -1.0)
            if not self.valid_node:
                return
            
            self.node_location = lat, lon
            self.attrs = attrs
            self.node_id = int(attrs['id'])
            self.node_ids.add(self.node_id)
            self.tags = {}
            
        elif name == 'tag' and self.valid_node:
            self.tags[attrs['k']] = attrs['v']
            
    def endElement(self, name):
        if name == 'node' and self.valid_node:
            if self.tags.get('amenity') in AMENITIES:
                #print self.node_location, self.tags['amenity']
                pass
            else:
                self.ignore_count += 1
                return
                
            entity, created = Entity.objects.get_or_create(osm_node_id=self.node_id)
            
            
            if created or not entity.metadata or entity.metadata.get('attrs', {}).get('timestamp', '') < self.attrs['timestamp']:
            
                if created:
                    self.create_count += 1
                else:
                    self.modify_count += 1

                entity_type = self.entity_types[self.tags['amenity']]
                entity.location = Point(self.node_location[1], self.node_location[0], srid=4326)
                try:
                    name = self.tags['name']
                except:
                    try:
                        name = ', '.join(reverse_geocode(*self.node_location)[0]['address'].split(', ')[:1])
                        name = "%s near %s" % (entity_type.verbose_name, name)
                    except:
                        name = "%s near %f,%f" % (entity_type.verbose_name, self.node_location[0], self.node_location[1])
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
        for entity in Entity.objects.filter(osm_node_id__isnull=False):
            if not entity.osm_node_id in self.node_ids:
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
        f = open(OSM_ETAG_FILENAME, 'r')
        etag = f.read()
        f.close()
        return etag
    except IOError:
        return None
def set_osm_etag(etag):
    f = open(OSM_ETAG_FILENAME, 'w')
    f.write(etag)
    f.close()

class AnyMethodRequest(urllib2.Request):
    def __init__(self, url, data=None, headers={}, origin_req_host=None, unverifiable=None, method=None):
        self.method = method and method.upper() or None
        urllib2.Request.__init__(self, url, data, headers, origin_req_host, unverifiable)

    def get_method(self):
        if not self.method is None:
            return self.method
        elif self.has_data():
            return "POST"
        else:
            return "GET"


class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list
    help = "Loads OpenStreetMap data."

    requires_model_validation = True
    
    ENGLAND_OSM_BZ2_URL = 'http://download.geofabrik.de/osm/europe/great_britain/england.osm.bz2'
    #ENGLAND_OSM_BZ2_URL = 'http://download.geofabrik.de/osm/europe/great_britain/england/shropshire.osm.bz2'

    SHELL_CMD_1 = "wget -O- %s --quiet | bunzip2" % ENGLAND_OSM_BZ2_URL
    SHELL_CMD_2 = ["bunzip"]

    def handle_noargs(self, **options):
        old_etag = get_osm_etag()
        
        request = AnyMethodRequest(Command.ENGLAND_OSM_BZ2_URL, method='HEAD')
        response = urllib2.urlopen(request)
        new_etag = response.headers['ETag'][1:-1]
        
        if new_etag == old_etag:
            print 'OSM data not updated. Not updating.'
            return
            
        p = popen2.popen2(Command.SHELL_CMD_1)
        
        parser = make_parser()
        parser.setContentHandler(OxfordHandler())
        parser.parse(p[0])
        
        set_osm_etag(new_etag)
