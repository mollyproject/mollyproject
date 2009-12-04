# -*- coding: utf-8 -*-
from django.core.management.base import NoArgsCommand
from django.contrib.gis.geos import Point, LineString, LinearRing
from django.conf import settings
from mobile_portal.oxpoints.models import Entity, EntityType
from mobile_portal.core.geolocation import reverse_geocode
from mobile_portal.core.models import Config
from mobile_portal.core.utils import AnyMethodRequest
from xml.sax import saxutils, handler, make_parser
import urllib2, bz2, subprocess, popen2, sys
from os import path

AMENITIES = {
    'bicycle_parking': (
        'a', 'bicycle rack', 'bicycle racks',
        True, False,
        (),
    ),
    'bank': (
        'a', 'bank', 'banks',
        True, True,
        (),
    ),
    'bar': (
        'a', 'bar', 'bars',
        True, True,
        (),
    ),
    'cinema': (
        'a', 'cinema', 'cinemas',
        True, True,
        (),
    ),
    'theatre': (
        'a', 'theatre', 'theatres',
        True, True,
        (),
    ),
    'post_box': (
        'a', 'post box', 'post boxes',
        True, False,
        (),
    ),
    'recycling': (
        'a', 'recycling facility', 'recycling facilities',
        True, False,
        (),
    ),
    'post_office': (
        'a', 'post office', 'post offices',
        True, False,
        (),
    ),
    'pharmacy': (
        'a', 'pharmacy', 'pharmacies',
        False, False,
        ('medical',),
    ),
    'hospital': (
        'a', 'hospital', 'hospitals',
        False, False,
        ('medical',),
    ),
    'doctors': (
        'a', "doctor's surgery", "doctors' surgeries",
        False, False,
        ('medical',),
    ), 
    'atm': (
        'an', 'ATM', 'ATMs',
        True, False,
        (),
    ),
    'parking': (
        'a', 'car park', 'car parks',
        True, False,
        (),
    ),
    'pub': (
        'a', 'pub', 'pubs',
        True, True,
        (),
    ),
    'ice_cream': (
        'an', 'ice cream café', 'ice cream cafés',
        False, False,
        ('cafe','food',),
    ),
    'cafe': (
        'a', 'café', 'cafés',
        False, False,
        ('food',),
    ),
    'restaurant': (
        'a', 'restaurant', 'restaurants',
        False, False,
        ('food',),
    ),
    'medical': (
        'a', 'place relating to health', 'places relating to health',
        True, True,
        (),
    ),
    'fast_food': (
        'a', 'fast food outlet', 'fast food outlets',
        False, False,
        ('food',),
    ),
    'food': (
        'a', 'place to eat', 'places to eat',
        True, True,
        (),
    ),
    'library': (
        'a', 'public library', 'public libraries',
        True, True,
        (),
    ),
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
        for slug, (article, verbose_name, verbose_name_plural, show_in_nearby_list, show_in_category_list, other_types) in AMENITIES.items():
            entity_type, created = EntityType.objects.get_or_create(slug=slug)
            entity_type.verbose_name = verbose_name
            entity_type.verbose_name_plural = verbose_name_plural
            entity_type.article = article
            entity_type.source = 'osm'
            entity_type.id_field = 'osm_id'
            entity_type.show_in_nearby_list = show_in_nearby_list
            entity_type.show_in_category_list = show_in_category_list
            entity_type.save()
            self.entity_types[slug] = entity_type
            
            entity_type.all_types = other_types + (slug,)
            
        for entity_type in self.entity_types.values():
            for s in entity_type.all_types:
                et = self.entity_types[s]
                et.sub_types.add(entity_type)
                
            entity_type.all_types = tuple(self.entity_types[slug] for slug in entity_type.all_types)

        for entity_type in self.entity_types.values():
            entity_type.save()
        
        self.create_count, self.modify_count = 0,0
        self.delete_count, self.unchanged_count = 0,0
        self.ignore_count = 0
        
        self.node_locations = {}
        
    def startElement(self, name, attrs):
        if name == 'node':
            lat, lon = float(attrs['lat']), float(attrs['lon'])
            
            self.valid = (51.5 < lat < 52.1 and -1.6 < lon < -1.0)
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

            # We already have these from OxPoints, so leave them alone.            
            if self.tags.get('amenity') == 'library' and self.tags.get('operator') == 'University of Oxford':
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
                    name = self.tags.get('name') or self.tags['operator']
                except (KeyError, AssertionError):
                    try:
                        name = reverse_geocode(*self.node_location)[0][0]
                        name = "Near %s" % (name)
                    except:
                        name = "Near %f, %f" % (self.node_location[0], self.node_location[1])

                entity.title = name
                entity.metadata = {
                    'attrs': dict(self.attrs),
                    'tags': self.tags
                }
                entity.entity_type = entity_type
                
                for et in entity_type.all_types:
                    entity.all_types.add(et)
                
                if self.tags.get('atm') == 'yes':
                    entity.all_types.add(self.entity_types['atm'])
                if self.tags.get('food') == 'yes':
                    entity.all_types.add(self.entity_types['food'])
                    
                entity.save()
                
            else:
                self.unchanged_count += 1
    
    def endDocument(self):
        for entity in Entity.objects.filter(osm_id__isnull=False):
            if not entity.osm_id in self.ids:
                entity.delete()
                self.delete_count += 1
                
        entities = Entity.objects.filter(osm_id__isnull=False)
        inferred_names = {}
        for entity in entities:
            inferred_name = entity.metadata['tags'].get('name') or entity.metadata['tags'].get('operator')
            if not inferred_name:
                continue
            if not inferred_name in inferred_names:
                inferred_names[inferred_name] = set()
            inferred_names[inferred_name].add(entity)
            
        for inferred_name, entities in inferred_names.items():
            if len(entities) > 1:
                for entity in entities:
                    try:
                        entity.title = "%s, %s" % (inferred_name, reverse_geocode(entity.location[1], entity.location[0])[0][0])
                        entity.save()
                    except:
                        print "Couldn't geocode for %s" % inferred_name
                        pass
            
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
#    SHELL_CMD = "cat /home/alex/gpsmid/england.osm.bz2 | bunzip2"
    
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
