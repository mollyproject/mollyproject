# -*- coding: utf-8 -*-
import urllib2
import bz2
import subprocess
import sys
import random
import os
import yaml

from xml.sax import saxutils, handler, make_parser

from django.contrib.gis.geos import Point, LineString, LinearRing
from django.conf import settings
from django.utils.translation import ugettext as _

from molly.apps.places.models import Entity, EntityType, Source, EntityTypeCategory
from molly.apps.places.providers import BaseMapsProvider
from molly.utils.misc import AnyMethodRequest, override
from molly.geolocation import reverse_geocode
from molly.conf.settings import batch

def node_id(id):
    return "N%d" % int(id)
def way_id(id):
    return "W%d" % int(id)

class OSMHandler(handler.ContentHandler):
    def __init__(self, source, entity_types, find_types, output, lat_north=None,
                 lat_south=None, lon_west=None, lon_east=None):
        self.source = source
        self.entity_types = entity_types
        self.find_types = find_types
        self.output = output
        self._lat_north = lat_north
        self._lat_south = lat_south
        self._lon_west = lon_west
        self._lon_east = lon_east

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

            # We already have these from OxPoints, so leave them alone.
            if self.tags.get('amenity') == 'library' and self.tags.get('operator') == 'University of Oxford':
                return

            # Ignore disused and under-construction entities
            if self.tags.get('life_cycle', 'in_use') != 'in_use' or self.tags.get('disused') in ('1', 'yes', 'true'):
                return

            try:
                entity = Entity.objects.get(source=self.source, _identifiers__scheme='osm', _identifiers__value=self.id)
                created = True
            except Entity.DoesNotExist:
                entity = Entity(source=self.source)
                created = False

            if not 'osm' in entity.metadata or entity.metadata['osm'].get('attrs', {}).get('timestamp', '') < self.attrs['timestamp']:

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

                try:
                    name = self.tags.get('name') or self.tags['operator']
                except (KeyError, AssertionError):
                    try:
                        name = reverse_geocode(*entity.location)[0]['name']
                        if not name:
                            raise IndexError
                        name = u"↝ %s" % name
                    except IndexError:
                        name = u"↝ %f, %f" % (self.node_location[1], self.node_location[0])

                entity.title = name
                entity.metadata['osm'] = {
                    'attrs': dict(self.attrs),
                    'tags': self.tags
                }
                entity.primary_type = self.entity_types[types[0]]

                if 'addr:postcode' in self.tags:
                    entity.post_code = self.tags['addr:postcode'].replace(' ', '')
                else:
                    entity.post_code = ""

                entity.save(identifiers={'osm': self.id})

                entity.all_types = [self.entity_types[et] for et in types]
                entity.update_all_types_completion()

            else:
                self.unchanged_count += 1

    def endDocument(self):
        for entity in Entity.objects.filter(source=self.source):
            if not entity.identifiers['osm'] in self.ids:
                entity.delete()
                self.delete_count += 1

        self.output.write("""\
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
    SHELL_CMD = "wget -O- %s --quiet | bunzip2"

    def __init__(self, lat_north=None, lat_south=None,
                 lon_west=None, lon_east=None,
                 url='http://download.geofabrik.de/osm/europe/great_britain/england.osm.bz2',
                 entity_type_data_file=None,
                 osm_tags_data_file=None):
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

    @batch('%d 9 * * mon' % random.randint(0, 59))
    def import_data(self, metadata, output):
        "Imports places data from OpenStreetMap"

        old_etag = metadata.get('etag', '')

        request = AnyMethodRequest(self._url, method='HEAD')
        response = urllib2.urlopen(request)
        new_etag = response.headers['ETag'][1:-1]

        if False and new_etag == old_etag:
            output.write('OSM data not updated. Not updating.\n')
            return

        p = subprocess.Popen([self.SHELL_CMD % self._url], shell=True,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True)

        parser = make_parser()
        parser.setContentHandler(OSMHandler(self._get_source(),
                                            self._get_entity_types(),
                                            lambda tags, type_list=None: self._find_types(t, self._osm_tags if type_list is None else type_list),
                                            output,
                                            self._lat_north,
                                            self._lat_south,
                                            self._lon_west,
                                            self._lon_east))
        parser.parse(p.stdout)
        
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
            entity_type, created = EntityType.objects.get_or_create(slug=slug)
            entity_type.slug = slug
            entity_type.category=et_category
            if created:
                entity_type.show_in_nearby_list = et['show_in_nearby_list']
                entity_type.show_in_category_list = et['show_in_category_list']
            entity_type.save()
            for lang_code, lang_name in settings.LANGUAGES:
                with override(lang_code):
                    name = entity_type.names.filter(language_code=lang_code)
                    if name.count() == 0:
                        entity_type.names.create(
                            language_code=lang_code,
                            verbose_name=_(et['verbose_name']),
                            verbose_name_singular=_(et['verbose_name_singular']),
                            verbose_name_plural=_(et['verbose_name_plural']))
                    else:
                        name = name[0]
                        name.verbose_name=_(et['verbose_name'])
                        name.verbose_name_singular=_(et['verbose_name_singular'])
                        name.verbose_name_plural=_(et['verbose_name_plural'])
                        name.save()
            new_entity_types.add(slug)
            entity_types[slug] = entity_type

        for slug in new_entity_types:
            subtype_of = self._entity_types[slug][5]
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
        entities = Entity.objects.filter(source=source)
        inferred_names = {}
        for entity in entities:
            inferred_name = entity.metadata['osm']['tags'].get('name') or entity.metadata['osm']['tags'].get('operator')
            if not inferred_name:
                continue
            if not inferred_name in inferred_names:
                inferred_names[inferred_name] = set()
            inferred_names[inferred_name].add(entity)

        for inferred_name, entities in inferred_names.items():
            if len(entities) > 1:
                for entity in entities:
                    if entity.metadata['osm']['tags'].get('addr:street'):
                        entity.title = u"%s, %s" % (inferred_name, entity.metadata['osm']['tags'].get('addr:street'))
                        continue

                    try:
                        name = reverse_geocode(entity.location[0], entity.location[1])[0]['name']
                        if name:
                            entity.title = u"%s, %s" % (inferred_name, name)
                            entity.save()
                    except:
                        self.output.write("Couldn't geocode for %s\n" % inferred_name)

if __name__ == '__main__':
    provider = OSMMapsProvider()
    provider.import_data()
