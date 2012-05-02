# -*- coding: utf-8 -*-
import urllib2
import bz2
import subprocess
import sys
import random
import os
import yaml
import logging

from xml.sax import saxutils, handler, make_parser
from datetime import timedelta

from django.db import reset_queries
from django.contrib.gis.geos import Point, LineString, LinearRing
from django.conf import settings
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_noop
from django.utils.translation import get_language

from molly.apps.places import get_entity
from molly.apps.places.models import (Entity, EntityType, Source,
                                      EntityTypeCategory, EntityName)
from molly.apps.places.providers import BaseMapsProvider
from molly.utils.misc import AnyMethodRequest
from molly.utils.i18n import override, set_name_in_language
from molly.geolocation import reverse_geocode
from molly.conf.provider import task


logger = logging.getLogger(__name__)

def node_id(id):
    return "N%d" % int(id)
def way_id(id):
    return "W%d" % int(id)

class OSMHandler(handler.ContentHandler):
    def __init__(self, source, entity_types, find_types, lat_north=None,
                 lat_south=None, lon_west=None, lon_east=None, identities={}):
        self.source = source
        self.entity_types = entity_types
        self.find_types = find_types
        self._lat_north = lat_north
        self._lat_south = lat_south
        self._lon_west = lon_west
        self._lon_east = lon_east
        self.identities = identities

    def startDocument(self):
        self.ids = set()
        self.tags = {}
        self.valid_node = True
        
        self.create_count, self.modify_count = 0,0
        self.delete_count, self.unchanged_count = 0,0
        self.ignore_count = 0
        
        self.node_locations = {}

    def startElement(self, name, attrs):
        
        if name == 'node':
            lon, lat = float(attrs['lon']), float(attrs['lat'])
            
            # Always import if restrictions aren't set
            if self._lat_north is None:
                self.valid = True
            else:
                self.valid = (self._lat_south < lat < self._lat_north \
                              and self._lon_west < lon < self._lon_east)
                if not self.valid:
                    return
            
            id = node_id(attrs['id'])
            self.node_location = lon, lat
            self.attrs = attrs
            self.id = id
            self.ids.add(id)
            self.tags = {}
            self.node_locations[id] = lon, lat
        
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
            try:
                types = self.find_types(self.tags)
            except ValueError:
                self.ignore_count += 1
                return
            
            # Ignore ways that lay partly outside our bounding box
            if name == 'way' and not all(id in self.node_locations for id in self.nodes):
                return
            
            # Ignore disused and under-construction entities
            if self.tags.get('life_cycle', 'in_use') != 'in_use' or self.tags.get('disused') in ('1', 'yes', 'true'):
                return
            
            # Memory management in debug mode
            reset_queries()
            
            if self.id in self.identities:
                entity = get_entity(*self.identities[self.id].split(':'))
                
                entity.metadata['osm'] = {
                    'attrs': dict(self.attrs),
                    'tags': dict(zip((k.replace(':', '_') for k in self.tags.keys()), self.tags.values()))
                }
                
                identifiers = entity.identifiers
                identifiers.update({
                    'osm': self.id
                })
                entity.save(identifiers=identifiers)
                entity.all_types = set(entity.all_types.all()) | set(self.entity_types[et] for et in types)
                entity.update_all_types_completion()
                self.ids.remove(self.id)
                
            else:
                try:
                    entity = Entity.objects.get(source=self.source,
                                                _identifiers__scheme='osm',
                                                _identifiers__value=self.id)
                    created = False
                except Entity.DoesNotExist:
                    entity = Entity(source=self.source)
                    created = True
            
                if not 'osm' in entity.metadata or \
                  entity.metadata['osm'].get('attrs', {}).get('timestamp', '') < self.attrs['timestamp']:
                    
                    if created:
                        self.create_count += 1
                    else:
                        self.modify_count += 1
                    
                    if name == 'node':
                        entity.location = Point(self.node_location, srid=4326)
                        entity.geometry = entity.location
                    elif name == 'way':
                        cls = LinearRing if self.nodes[0] == self.nodes[-1] else LineString
                        entity.geometry = cls([self.node_locations[n] for n in self.nodes], srid=4326)
                        min_, max_ = (float('inf'), float('inf')), (float('-inf'), float('-inf'))
                        for lon, lat in [self.node_locations[n] for n in self.nodes]:
                            min_ = min(min_[0], lon), min(min_[1], lat) 
                            max_ = max(max_[0], lon), max(max_[1], lat)
                        entity.location = Point( (min_[0]+max_[0])/2 , (min_[1]+max_[1])/2 , srid=4326)
                    else:
                        raise AssertionError("There should be no other types of entity we're to deal with.")
                    
                    names = dict()
                    
                    for lang_code, lang_name in settings.LANGUAGES:
                        with override(lang_code):
                        
                            if '-' in lang_code:
                                tags_to_try = ('name:%s' % lang_code, 'name:%s' % lang_code.split('-')[0], 'name', 'operator')
                            else:
                                tags_to_try = ('name:%s' % lang_code, 'name', 'operator')
                                name = None
                                for tag_to_try in tags_to_try:
                                    if self.tags.get(tag_to_try):
                                        name = self.tags.get(tag_to_try)
                                        break
                            
                            if name is None:
                                try:
                                    name = reverse_geocode(*entity.location)[0]['name']
                                    if not name:
                                        raise IndexError
                                    name = u"↝ %s" % name
                                except IndexError:
                                    name = u"↝ %f, %f" % (self.node_location[1], self.node_location[0])
                            
                            names[lang_code] = name
                    
                    entity.metadata['osm'] = {
                        'attrs': dict(self.attrs),
                        'tags': dict(zip((k.replace(':', '_') for k in self.tags.keys()), self.tags.values()))
                    }
                    entity.primary_type = self.entity_types[types[0]]
                    
                    identifiers = entity.identifiers
                    identifiers.update({
                        'osm': self.id
                    })
                    entity.save(identifiers=identifiers)
                    
                    for lang_code, name in names.items():
                        set_name_in_language(entity, lang_code, title=name)
                    
                    entity.all_types = [self.entity_types[et] for et in types]
                    entity.update_all_types_completion()
                
                else:
                    self.unchanged_count += 1

    def endDocument(self):
        for entity in Entity.objects.filter(source=self.source):
            if entity.identifiers.get('osm') not in self.ids:
                entity.delete()
                self.delete_count += 1
        
        logger.info("""\
Complete
  Created:   %6d
  Modified:  %6d
  Deleted:   %6d
  Unchanged: %6d
  Ignored:   %6d
""" % (
            self.create_count,
            self.modify_count,
            self.delete_count,
            self.unchanged_count,
            self.ignore_count,
        ))

class OSMMapsProvider(BaseMapsProvider):

    def __init__(self, lat_north=None, lat_south=None,
                 lon_west=None, lon_east=None,
                 url='http://download.geofabrik.de/osm/europe/great_britain/england.osm.bz2',
                 entity_type_data_file=None,
                 osm_tags_data_file=None,
                 identities_file=None):
        """
        @param lat_north: A limit of the northern-most latitude to import points
                          for
        @type lat_north: float
        @param lat_south: A limit of the southern-most latitude to import points
                          for
        @type lat_south: float
        @param lon_west: A limit of the western-most longitude to import points
                          for
        @type lon_west: float
        @param lon_east: A limit of the eastern-most longitude to import points
                          for
        @type lon_east: float
        @param url: The URL of the OSM planet file to download (defaults to
                    England)
        @type url: str
        @param entity_type_data_file: A YAML file defining the entity types
                                      which the OSM importer should create
        @type entity_type_data_file: str
        @param osm_tags_data_file: A YAML file defining the OSM tags which
                                   should be imported, and how these map to
                                   Molly's entity types
        @type osm_tags_data_file: str
        @param identities_file: A YAML file containing a mapping from OSM IDs
                                to any other namespace of entities. When an ID
                                is matched in this file, a new entitity is not
                                created, but instead associated with the other one
        @type identities_file: str
        """
        self._lat_north = lat_north
        self._lat_south = lat_south
        self._lon_west = lon_west
        self._lon_east = lon_east
        self._url = url
        
        if entity_type_data_file is None:
            entity_type_data_file = os.path.join(os.path.dirname(__file__),
                                                 '..', 'data', 'osm-entity-types.yaml')
        with open(entity_type_data_file) as fd:
            self._entity_types = yaml.load(fd)
            
        if osm_tags_data_file is None:
            osm_tags_data_file = os.path.join(os.path.dirname(__file__),
                                                 '..', 'data', 'osm-tags.yaml')
        with open(osm_tags_data_file) as fd:
            def to_tuple(tag):
                """
                Converts the new-style OSM tag file into the old-style tuple
                representation
                """
                if 'subtags' in tag:
                    return (tag['osm-tag'],
                            map(to_tuple, tag['subtags']),
                            tag['entity-type'])
                else:
                    return (tag['osm-tag'],
                            tag['entity-type'])
            self._osm_tags = map(to_tuple, yaml.load(fd))
        
        if identities_file is not None:
            with open(identities_file) as fd:
                self.identities = yaml.load(fd)
        else:
            self.identities = {}

    @task(run_every=timedelta(days=7))
    def import_data(self, **metadata):
        "Imports places data from OpenStreetMap"
        
        old_etag = metadata.get('etag', '')
        
        request = AnyMethodRequest(self._url, method='HEAD')
        response = urllib2.urlopen(request)
        new_etag = response.headers['ETag'][1:-1]
        
        if not settings.DEBUG and new_etag == old_etag:
            logger.info('OSM data not updated. Not updating.\n')
            return
        
        parser = make_parser(['xml.sax.xmlreader.IncrementalParser'])
        parser.setContentHandler(OSMHandler(self._get_source(),
                                            self._get_entity_types(),
                                            lambda tags, type_list=None: self._find_types(tags, self._osm_tags if type_list is None else type_list),
                                            self._lat_north,
                                            self._lat_south,
                                            self._lon_west,
                                            self._lon_east,
                                            self.identities))
        
        # Parse in 8k chunks
        osm = urllib2.urlopen(self._url)
        buffer = osm.read(8192)
        bunzip = bz2.BZ2Decompressor()
        while buffer:
            parser.feed(bunzip.decompress(buffer))
            buffer = osm.read(8192)
        parser.close()
        
        for lang_code, lang_name in settings.LANGUAGES:
            with override(lang_code):
                self.disambiguate_titles(self._get_source())
        
        return {
            'etag': new_etag,
        }

    def _get_source(self):
        try:
            source = Source.objects.get(module_name="molly.providers.apps.maps.osm")
        except Source.DoesNotExist:
            source = Source(module_name="molly.providers.apps.maps.osm")
        
        source.name = "OpenStreetMap"
        source.save()
        
        return source

    def _get_entity_types(self):
        
        entity_types = {}
        new_entity_types = set()
        for slug, et in self._entity_types.items():
            et_category, created = EntityTypeCategory.objects.get_or_create(name=et['category'])
            try:
                entity_type = EntityType.objects.get(slug=slug)
                created = False
            except EntityType.DoesNotExist:
                entity_type = EntityType(slug=slug)
                created = True
            entity_type.category = et_category
            entity_type.slug = slug
            if created:
                entity_type.show_in_nearby_list = et['show_in_nearby_list']
                entity_type.show_in_category_list = et['show_in_category_list']
            entity_type.save()
            for lang_code, lang_name in settings.LANGUAGES:
                with override(lang_code):
                    set_name_in_language(entity_type, lang_code,
                                         verbose_name=_(et['verbose_name']),
                                         verbose_name_singular=_(et['verbose_name_singular']),
                                         verbose_name_plural=_(et['verbose_name_plural']))
            new_entity_types.add(slug)
            entity_types[slug] = entity_type
        
        for slug in new_entity_types:
            subtype_of = self._entity_types[slug]['parent-types']
            entity_types[slug].subtype_of.clear()
            for s in subtype_of:
                entity_types[slug].subtype_of.add(entity_types[s])
            entity_types[slug].save()
        
        return entity_types

    def _find_types(self, tags, type_list):
        found_types = []
        for item in type_list:
            tag, value = item[0].split('=')
            if tags.get(tag) == value:
                if len(item) == 2:
                    found_types.append(item[1])
                else:
                    try:
                        found_types += self._find_types(tags, item[1])
                    except ValueError:
                        found_types.append(item[2])
        if found_types:
            return found_types
        else:
            raise ValueError

    def disambiguate_titles(self, source):
        lang_code = get_language()
        entities = Entity.objects.filter(source=source)
        inferred_names = {}
        if '-' in lang_code:
            tags_to_try = ('name-%s' % lang_code, 'name-%s' % lang_code.split('-')[0], 'name', 'operator')
        else:
            tags_to_try = ('name-%s' % lang_code, 'name', 'operator')
        for entity in entities:
            inferred_name = None
            for tag_to_try in tags_to_try:
                if entity.metadata['osm']['tags'].get(tag_to_try):
                    inferred_name = entity.metadata['osm']['tags'].get(tag_to_try)
                    break
            if not inferred_name:
                continue
            if not inferred_name in inferred_names:
                inferred_names[inferred_name] = set()
            inferred_names[inferred_name].add(entity)
        
        for inferred_name, entities in inferred_names.items():
            if len(entities) > 1:
                for entity in entities:
                    if entity.metadata['osm']['tags'].get('addr_street'):
                        title = u"%s, %s" % (inferred_name, entity.metadata['osm']['tags'].get('addr_street'))
                    else:
                        try:
                            place_name = reverse_geocode(entity.location[0], entity.location[1])[0]['name']
                            if place_name:
                                title = u"%s, %s" % (inferred_name, place_name)
                                entity.save()
                            else:
                                title = inferred_name
                        except:
                            logger.info("Couldn't geocode for %s\n" % inferred_name)
                            title = inferred_name
                    try:
                        name = entity.names.get(language_code=lang_code)
                    except EntityName.DoesNotExist:
                        name = entity.names.create(language_code=lang_code,
                                                   title=title)
                    else:
                        name.title = title
                    finally:
                        name.save()

if __name__ == '__main__':
    provider = OSMMapsProvider()
    provider.import_data()

# IGNORE BELOW HERE! These are dummy EntityType definitions that exist so they
# get picked up as ready to translate
# THIS CODE DOES NOTHING, CHANGING HERE WON'T DO WHAT YOU THINK IT DOES
DUMMY = {
    'atm': {
        'category': ugettext_noop('Amenities'),
        'verbose_name': ugettext_noop('ATM'),
        'verbose_name_plural': ugettext_noop('ATMs'),
        'verbose_name_singular': ugettext_noop('an ATM')
    },
    'bank': {
        'category': ugettext_noop('Amenities'),
        'verbose_name': ugettext_noop('bank'),
        'verbose_name_plural': ugettext_noop('banks'),
        'verbose_name_singular': ugettext_noop('a bank')
    },
    'bar': {
        'category': ugettext_noop('Amenities'),
        'verbose_name': ugettext_noop('bar'),
        'verbose_name_plural': ugettext_noop('bars'),
        'verbose_name_singular': ugettext_noop('a bar')
    },
    'bench': {
        'category': ugettext_noop('Amenities'),
        'verbose_name': ugettext_noop('bench'),
        'verbose_name_plural': ugettext_noop('benches'),
        'verbose_name_singular': ugettext_noop('a bench')
    },
    'bicycle-parking': {
        'category': ugettext_noop('Transport'),
        'verbose_name': ugettext_noop('bicycle rack'),
        'verbose_name_plural': ugettext_noop('bicycle racks'),
        'verbose_name_singular': ugettext_noop('a bicycle rack')
    },
    'cafe': {
        'category': ugettext_noop('Amenities'),
        'verbose_name': ugettext_noop(u'café'),
        'verbose_name_plural': ugettext_noop(u'cafés'),
        'verbose_name_singular': ugettext_noop(u'a café')
    },
    'car-park': {
        'category': ugettext_noop('Transport'),
        'verbose_name': ugettext_noop('car park'),
        'verbose_name_plural': ugettext_noop('car parks'),
        'verbose_name_singular': ugettext_noop('a car park')
    },
    'cathedral': {
        'category': ugettext_noop('Amenities'),
        'verbose_name': ugettext_noop('cathedral'),
        'verbose_name_plural': ugettext_noop('cathedrals'),
        'verbose_name_singular': ugettext_noop('a cathedral')
    },
    'chapel': {
        'category': ugettext_noop('Amenities'),
        'verbose_name': ugettext_noop('chapel'),
        'verbose_name_plural': ugettext_noop('chapels'),
        'verbose_name_singular': ugettext_noop('a chapel')
    },
    'church': {
        'category': ugettext_noop('Amenities'),
        'verbose_name': ugettext_noop('church'),
        'verbose_name_plural': ugettext_noop('churches'),
        'verbose_name_singular': ugettext_noop('a church')
    },
    'cinema': {
        'category': ugettext_noop('Leisure'),
        'verbose_name': ugettext_noop('cinema'),
        'verbose_name_plural': ugettext_noop('cinemas'),
        'verbose_name_singular': ugettext_noop('a cinema')
    },
    'cycle-shop': {
        'category': ugettext_noop('Amenities'),
        'verbose_name': ugettext_noop('cycle shop'),
        'verbose_name_plural': ugettext_noop('cycle shops'),
        'verbose_name_singular': ugettext_noop('a cycle shop')
    },
    'dispensing-pharmacy': {
        'category': ugettext_noop('Amenities'),
        'verbose_name': ugettext_noop('dispensing pharmacy'),
        'verbose_name_plural': ugettext_noop('dispensing pharmacies'),
        'verbose_name_singular': ugettext_noop('a dispensing pharmacy')
    },
    'doctors': {
        'category': ugettext_noop('Amenities'),
        'verbose_name': ugettext_noop("doctor's surgery"),
        'verbose_name_plural': ugettext_noop("doctors' surgeries"),
        'verbose_name_singular': ugettext_noop("a doctor's surgery")
    },
    'fast-food': {
        'category': ugettext_noop('Amenities'),
        'verbose_name': ugettext_noop('fast food outlet'),
        'verbose_name_plural': ugettext_noop('fast food outlets'),
        'verbose_name_singular': ugettext_noop('a fast food outlet')
    },
    'food': {
        'category': ugettext_noop('Amenities'),
        'verbose_name': ugettext_noop('place to eat'),
        'verbose_name_plural': ugettext_noop('places to eat'),
        'verbose_name_singular': ugettext_noop('a place to eat')
    },
    'hospital': {
        'category': ugettext_noop('Amenities'),
        'verbose_name': ugettext_noop('hospital'),
        'verbose_name_plural': ugettext_noop('hospitals'),
        'verbose_name_singular': ugettext_noop('a hospital')
    },
    'ice-cream': {
        'category': ugettext_noop('Amenities'),
        'verbose_name': ugettext_noop(u'ice cream café'),
        'verbose_name_plural': ugettext_noop(u'ice cream cafés'),
        'verbose_name_singular': ugettext_noop(u'an ice cream café')
    },
    'ice-rink': {
        'category': ugettext_noop('Leisure'),
        'verbose_name': ugettext_noop('ice rink'),
        'verbose_name_plural': ugettext_noop('ice rinks'),
        'verbose_name_singular': ugettext_noop('an ice rink')
    },
    'library': {
        'category': ugettext_noop('Amenities'),
        'verbose_name': ugettext_noop('library'),
        'verbose_name_plural': ugettext_noop('libraries'),
        'verbose_name_singular': ugettext_noop('a library')
    },
    'mandir': {
        'category': ugettext_noop('Amenities'),
        'verbose_name': ugettext_noop('mandir'),
        'verbose_name_plural': ugettext_noop('mandirs'),
        'verbose_name_singular': ugettext_noop('a mandir')
    },
    'medical': {
        'category': ugettext_noop('Amenities'),
        'verbose_name': ugettext_noop('place relating to health'),
        'verbose_name_plural': ugettext_noop('places relating to health'),
        'verbose_name_singular': ugettext_noop('a place relating to health')
    },
    'mosque': {
        'category': ugettext_noop('Amenities'),
        'verbose_name': ugettext_noop('mosque'),
        'verbose_name_plural': ugettext_noop('mosques'),
        'verbose_name_singular': ugettext_noop('a mosque')
    },
    'museum': {
        'category': ugettext_noop('Leisure'),
        'verbose_name': ugettext_noop('museum'),
        'verbose_name_plural': ugettext_noop('museums'),
        'verbose_name_singular': ugettext_noop('a museum')
    },
    'park': {
        'category': ugettext_noop('Leisure'),
        'verbose_name': ugettext_noop('park'),
        'verbose_name_plural': ugettext_noop('parks'),
        'verbose_name_singular': ugettext_noop('a park')
    },
    'park-and-ride': {
        'category': ugettext_noop('Transport'),
        'verbose_name': ugettext_noop('park and ride'),
        'verbose_name_plural': ugettext_noop('park and rides'),
        'verbose_name_singular': ugettext_noop('a park and ride')
    },
    'pharmacy': {
        'category': ugettext_noop('Amenities'),
        'verbose_name': ugettext_noop('pharmacy'),
        'verbose_name_plural': ugettext_noop('pharmacies'),
        'verbose_name_singular': ugettext_noop('a pharmacy')
    },
    'place-of-worship': {
        'category': ugettext_noop('Amenities'),
        'verbose_name': ugettext_noop('place of worship'),
        'verbose_name_plural': ugettext_noop('places of worship'),
        'verbose_name_singular': ugettext_noop('a place of worship')
    },
    'post-box': {
        'category': ugettext_noop('Amenities'),
        'verbose_name': ugettext_noop('post box'),
        'verbose_name_plural': ugettext_noop('post boxes'),
        'verbose_name_singular': ugettext_noop('a post box')
    },
    'post-office': {
        'category': ugettext_noop('Amenities'),
        'verbose_name': ugettext_noop('post office'),
        'verbose_name_plural': ugettext_noop('post offices'),
        'verbose_name_singular': ugettext_noop('a post office')
    },
    'pub': {
        'category': ugettext_noop('Amenities'),
        'verbose_name': ugettext_noop('pub'),
        'verbose_name_plural': ugettext_noop('pubs'),
        'verbose_name_singular': ugettext_noop('a pub')
    },
    'public-library': {
        'category': ugettext_noop('Amenities'),
        'verbose_name': ugettext_noop('public library'),
        'verbose_name_plural': ugettext_noop('public libraries'),
        'verbose_name_singular': ugettext_noop('a public library')
    },
    'punt-hire': {
        'category': ugettext_noop('Leisure'),
        'verbose_name': ugettext_noop('place to hire punts'),
        'verbose_name_plural': ugettext_noop('places to hire punts'),
        'verbose_name_singular': ugettext_noop('a place to hire punts')
    },
    'recycling': {
        'category': ugettext_noop('Amenities'),
        'verbose_name': ugettext_noop('recycling facility'),
        'verbose_name_plural': ugettext_noop('recycling facilities'),
        'verbose_name_singular': ugettext_noop('a recycling facility')
    },
    'restaurant': {
        'category': ugettext_noop('Amenities'),
        'verbose_name': ugettext_noop('restaurant'),
        'verbose_name_plural': ugettext_noop('restaurants'),
        'verbose_name_singular': ugettext_noop('a restaurant')
    },
    'shop': {
        'category': ugettext_noop('Amenities'),
        'verbose_name': ugettext_noop('shop'),
        'verbose_name_plural': ugettext_noop('shops'),
        'verbose_name_singular': ugettext_noop('a shop')
    },
    'sport': {
        'category': ugettext_noop('Leisure'),
        'verbose_name': ugettext_noop('place relating to sport'),
        'verbose_name_plural': ugettext_noop('places relating to sport'),
        'verbose_name_singular': ugettext_noop('a place relating to sport')
    },
    'sports-centre': {
        'category': ugettext_noop('Leisure'),
        'verbose_name': ugettext_noop('sports centre'),
        'verbose_name_plural': ugettext_noop('sports centres'),
        'verbose_name_singular': ugettext_noop('a sports centre')
    },
    'swimming-pool': {
        'category': ugettext_noop('Leisure'),
        'verbose_name': ugettext_noop('swimming pool'),
        'verbose_name_plural': ugettext_noop('swimming pools'),
        'verbose_name_singular': ugettext_noop('a swimming pool')
    },
    'synagogue': {
        'category': ugettext_noop('Amenities'),
        'verbose_name': ugettext_noop('synagogue'),
        'verbose_name_plural': ugettext_noop('synagogues'),
        'verbose_name_singular': ugettext_noop('a synagogue')
    },
    'taxi-rank': {
        'category': ugettext_noop('Transport'),
        'verbose_name': ugettext_noop('taxi rank'),
        'verbose_name_plural': ugettext_noop('taxi ranks'),
        'verbose_name_singular': ugettext_noop('a taxi rank')
    },
    'theatre': {
        'category': ugettext_noop('Leisure'),
        'verbose_name': ugettext_noop('theatre'),
        'verbose_name_plural': ugettext_noop('theatres'),
        'verbose_name_singular': ugettext_noop('a theatre')
    },
    'tourist-information': {
        'category': ugettext_noop('Leisure'),
        'verbose_name': ugettext_noop('tourist information point'),
        'verbose_name_plural': ugettext_noop('tourist information points'),
        'verbose_name_singular': ugettext_noop('a tourist information point')
    },
    'tourist-attraction': {
        'category': ugettext_noop('Leisure'),
        'verbose_name': ugettext_noop('tourist attraction'),
        'verbose_name_plural': ugettext_noop('tourist attractions'),
        'verbose_name_singular': ugettext_noop('a tourist attraction')
    },
}
