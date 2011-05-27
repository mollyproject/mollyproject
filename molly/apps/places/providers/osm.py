# -*- coding: utf-8 -*-
from django.contrib.gis.geos import Point, LineString, LinearRing
from django.conf import settings

from molly.apps.places.models import Entity, EntityType, Source, EntityTypeCategory
from molly.apps.places.providers import BaseMapsProvider
from molly.utils.misc import AnyMethodRequest
from molly.geolocation import reverse_geocode
from molly.conf.settings import batch

from xml.sax import saxutils, handler, make_parser
import urllib2, bz2, subprocess, sys, random
from os import path

def node_id(id):
    return "N%d" % int(id)
def way_id(id):
    return "W%d" % int(id)

class OSMHandler(handler.ContentHandler):
    def __init__(self, source, entity_types, find_types, output, lat_north=None, lat_south=None, lon_west=None, lon_east=None):
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
                self.valid = (self._lat_south < lat < self._lat_north and self._lon_west < lon < self._lon_east)
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
                    'tags': dict(zip((k.replace(':', '_') for k in self.tags.keys()), self.tags.values()))
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

    def __init__(self, lat_north=None, lat_south=None, lon_west=None, lon_east=None, url='http://download.geofabrik.de/osm/europe/great_britain/england.osm.bz2'):
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
        """
        self._lat_north = lat_north
        self._lat_south = lat_south
        self._lon_west = lon_west
        self._lon_east = lon_east
        self._url = url

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

        p = subprocess.Popen([self.SHELL_CMD % self._url], shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True)

        parser = make_parser()
        parser.setContentHandler(OSMHandler(self._get_source(),
                                            self._get_entity_types(),
                                            self._find_types,
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
        ENTITY_TYPES = {
            'atm':                 ('an', 'ATM',                      'ATMs',                      True,  False, (),                    'Amenities'),
            'bank':                ('a',  'bank',                     'banks',                     True,  True,  (),                    'Amenities'),
            'bench':               ('a',  'bench',                    'benches',                   True,  False, (),                    'Amenities'),
            'bar':                 ('a',  'bar',                      'bars',                      True,  True,  (),                    'Amenities'),
            'bicycle-parking':     ('a',  'bicycle rack',             'bicycle racks',             True,  False, (),                    'Transport'),
            'cafe':                ('a',  'café',                     'cafés',                     False, False, ('food',),             'Amenities'),
            'car-park':            ('a',  'car park',                 'car parks',                 False, False, (),                    'Transport'),
            'cathedral':           ('a',  'cathedral',                'cathedrals',                False, False, ('place-of-worship',), 'Amenities'),
            'chapel':              ('a',  'chapel',                   'chapels',                   False, False, ('place-of-worship',), 'Amenities'),
            'church':              ('a',  'church',                   'churches',                  False, False, ('place-of-worship',), 'Amenities'),
            'cinema':              ('a',  'cinema',                   'cinemas',                   True,  True,  (),                    'Leisure'),
            'cycle-shop':          ('a',  'cycle shop',               'cycle shops',               False, False, ('shop',),             'Amenities'),
            'dispensing-pharmacy': ('a',  'dispensing pharmacy',      'dispensing pharmacies',     False, False, ('pharmacy',),         'Amenities'),
            'doctors':             ('a',  "doctor's surgery",         "doctors' surgeries",        False, False, ('medical',),          'Amenities'),
            'fast-food':           ('a',  'fast food outlet',         'fast food outlets',         False, False, ('food',),             'Amenities'),
            'food':                ('a',  'place to eat',             'places to eat',             True,  True,  (),                    'Amenities'),
            'hospital':            ('a',  'hospital',                 'hospitals',                 False, False, ('medical',),          'Amenities'),
            'ice-cream':           ('an', 'ice cream café',           'ice cream cafés',           False, False, ('cafe','food',),      'Amenities'),
            'ice-rink':            ('an', 'ice rink',                 'ice rinks',                 False, False, ('sport',),            'Leisure'),
            'library':             ('a',  'library',                  'libraries',                 True,  True,  (),                    'Amenities'),
            'mandir':              ('a',  'mandir',                   'mandirs',                   False, False, ('place-of-worship',), 'Amenities'),
            'medical':             ('a',  'place relating to health', 'places relating to health', True,  True,  (),                    'Amenities'),
            'mosque':              ('a',  'mosque',                   'mosques',                   False, False, ('place-of-worship',), 'Amenities'),
            'museum':              ('a',  'museum',                   'museums',                   False, False, (),                    'Leisure'),
            'car-park':            ('a',  'car park',                 'car parks',                 True,  False, (),                    'Transport'),
            'park':                ('a',  'park',                     'parks',                     False, False, (),                    'Leisure'),
            'park-and-ride':       ('a',  'park and ride',            'park and rides',            False, False, ('car-park',),         'Transport'),
            'pharmacy':            ('a',  'pharmacy',                 'pharmacies',                False, False, ('medical',),          'Amenities'),
            'place-of-worship':    ('a',  'place of worship',         'places of worship',         False, False, (),                    'Amenities'),
            'post-box':            ('a',  'post box',                 'post boxes',                True,  False, (),                    'Amenities'),
            'post-office':         ('a',  'post office',              'post offices',              True,  False, (),                    'Amenities'),
            'pub':                 ('a',  'pub',                      'pubs',                      True,  True,  (),                    'Amenities'),
            'public-library':      ('a',  'public library',           'public libraries',          True,  True,  ('library',),          'Amenities'),
            'punt-hire':           ('a',  'place to hire punts',      'places to hire punts',      False, False, (),                    'Leisure'),
            'recycling':           ('a',  'recycling facility',       'recycling facilities',      True,  False, (),                    'Amenities'),
            'restaurant':          ('a',  'restaurant',               'restaurants',               False, False, ('food',),             'Amenities'),
            'shop':                ('a',  'shop',                     'shops',                     False, False, (),                    'Amenities'),
            'sport':               ('a',  'place relating to sport',  'places relating to sport',  False, False, (),                    'Leisure'),
            'sports-centre':       ('a',  'sports centre',            'sports centres',            False, False, ('sport',),            'Leisure'),
            'swimming-pool':       ('a',  'swimming pool',            'swimming pools',            False, False, ('sport',),            'Leisure'),
            'synagogue':           ('a',  'synagogue',                'synagogues',                False, False, ('place-of-worship',), 'Amenities'),
            'taxi-rank':           ('a',  'taxi rank',                'taxi ranks',                False, False, (),                    'Transport'),
            'theatre':             ('a',  'theatre',                  'theatres',                  True,  True,  (),                    'Leisure'),
        }

        entity_types = {}
        new_entity_types = set()
        for slug, (article, verbose_name, verbose_name_plural, nearby, category, subtype_of, et_category) in ENTITY_TYPES.items():
            et_category, _ = EntityTypeCategory.objects.get_or_create(name=et_category)
            try:
                entity_type = EntityType.objects.get(slug=slug)
                created = False
            except EntityType.DoesNotExist:
                entity_type = EntityType(slug=slug)
                created = True
            entity_type.slug = slug
            entity_type.category=et_category
            entity_type.verbose_name = verbose_name
            entity_type.verbose_name_plural = verbose_name_plural
            entity_type.article = 'a'
            if created:
                entity_type.show_in_nearby_list = nearby
                entity_type.show_in_category_list = category
            entity_type.save()
            new_entity_types.add(slug)
            entity_types[slug] = entity_type

        for slug in new_entity_types:
            subtype_of = ENTITY_TYPES[slug][5]
            entity_types[slug].subtype_of.clear()
            for s in subtype_of:
                entity_types[slug].subtype_of.add(entity_types[s])
            entity_types[slug].save()

        return entity_types

    OSM_TYPES = [
        ('amenity=place_of_worship', [
            ('place_of_worship=chapel', 'chapel'),
            ('place_of_worship=church', 'church'),
            ('place_of_worship=cathedral', 'cathedral'),
            ('religion=christian', 'church'),
            ('religion=muslim', 'mosque'),
            ('religion=hindu', 'mandir'),
            ('religion=jewish', 'synagogue'),
        ], 'place-of-worship'),
        ('amenity=ice_cream', 'ice-cream'),
        ('amenity=cafe', 'cafe'),
        ('amenity=atm', 'atm'),
        ('amenity=bank', 'bank'),
        ('amenity=bar', 'bar'),
        ('amenity=bench', 'bench'),
        ('amenity=bicycle_parking', 'bicycle-parking'),
        ('amenity=cinema', 'cinema'),
        ('amenity=doctors', 'doctors'),
        ('amenity=fast_food', 'fast-food'),
        ('amenity=hospital', 'hospital'),
        ('amenity=punt_hire', 'punt-hire'),
        ('amenity=library', 'library'),
        ('amenity=museum', 'museum'),
        ('amenity=parking', [
            ('park_ride=bus', 'park-and-ride'),
        ], 'car-park'),
        ('amenity=pharmacy', [
            ('dispensing=yes', 'dispensing-pharmacy'),
        ], 'pharmacy'),
        ('amenity=post_box', 'post-box'),
        ('amenity=post_office', 'post-office'),
        ('amenity=pub', 'pub'),
        ('amenity=recycling', 'recycling'),
        ('amenity=restaurant', 'restaurant'),
        ('amenity=theatre', 'theatre'),
        ('amenity=taxi', 'taxi-rank'),
        ('food=yes', 'food'),
        ('atm=yes', 'atm'),
        ('leisure=park', 'park'),
        ('leisure=sports_centre', 'sports-centre'),
        ('leisure=ice_rink', 'ice-rink'),
        ('sport=swimming', 'swimming-pool'),
        ('leisure=swimming_pool', 'swimming-pool'),
        ('shop=bicycle', 'cycle-shop'),
    ]

    def _find_types(self, tags, type_list=OSM_TYPES):
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
                    if entity.metadata['osm']['tags'].get('addr_street'):
                        entity.title = u"%s, %s" % (inferred_name, entity.metadata['osm']['tags'].get('addr_street'))
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
