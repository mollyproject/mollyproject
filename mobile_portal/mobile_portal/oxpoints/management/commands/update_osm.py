# -*- coding: utf-8 -*-
from django.core.management.base import NoArgsCommand
from django.contrib.gis.geos import Point
from mobile_portal.oxpoints.models import Entity, EntityType
from mobile_portal.core.geolocation import reverse_geocode

from xml.sax import saxutils, handler, make_parser

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
                print self.node_location, self.tags['amenity']
            else:
                return
                
            entity, created = Entity.objects.get_or_create(osm_node_id=self.node_id)

            if created or not entity.metadata or entity.metadata.get('attrs', {}).get('timestamp', '') < self.attrs['timestamp']:
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
    
    def endDocument(self):
        for entity in Entity.objects.filter(osm_node_id__isnull=False):
            if not entity.osm_node_id in self.node_ids:
                entity.delete()

class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list
    help = "Loads OpenStreetMap data."

    requires_model_validation = True
    
    ENGLAND_OSM_BZ2_URL = 'http://download.geofabrik.de/osm/europe/great_britain/england.osm.bz2'

    def handle_noargs(self, **options):
    
        print "Downloading data from download.geofabrik.de"
        
        parser = make_parser()
        parser.setContentHandler(OxfordHandler())
        parser.parse('/Erewhon/mobile_portal/mobile_portal/oxpoints/data/england.osm')
