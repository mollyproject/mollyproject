# -*- coding: utf-8 -*-
from django.contrib.gis.geos import Point, LineString, LinearRing
from django.conf import settings
from molly.apps.places.models import Entity, EntityType, Source
from molly.apps.places.providers import BaseMapsProvider
from molly.core.models import Config
from molly.utils.misc import AnyMethodRequest
from xml.sax import saxutils, handler, make_parser
import urllib2, bz2, subprocess, popen2, sys
from os import path


ENGLAND_OSM_BZ2_XML = 'http://download.geofabrik.de/osm/europe/great_britain/england.osm.bz2'
OSM_ETAG_FILENAME = path.join(settings.CACHE_DIR, 'osm_england_extract_etag')

def node_id(id):
    return "N%d" % int(id)
def way_id(id):
    return "W%d" % int(id)

class OSMHandler(handler.ContentHandler):
    def __init__(self, source, entity_types, find_types):
        self.source = source
        self.entity_types = entity_types
        self.find_types = find_types

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

            if True or not 'osm' in entity.metadata or entity.metadata['osm'].get('attrs', {}).get('timestamp', '') < self.attrs['timestamp']:

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

                try:
                    name = self.tags.get('name') or self.tags['operator']
                except (KeyError, AssertionError):
                    try:
                        name = reverse_geocode(*self.node_location)[0][0]
                        name = "Near %s" % (name)
                    except:
                        name = "Near %f, %f" % (self.node_location[0], self.node_location[1])

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

        entities = Entity.objects.filter(source=self.source)
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
                    entity.title = "%s, %s" % (inferred_name, entity.metadata['osm']['tags'].get('addr:street'))
                    continue

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

class OSMMapsProvider(BaseMapsProvider):
    ENGLAND_OSM_BZ2_URL = 'http://download.geofabrik.de/osm/europe/great_britain/england.osm.bz2'
    #ENGLAND_OSM_BZ2_URL = 'http://download.geofabrik.de/osm/europe/great_britain/england/shropshire.osm.bz2'

    SHELL_CMD = "wget -O- %s --quiet | bunzip2" % ENGLAND_OSM_BZ2_URL
#    SHELL_CMD = "cat /home/alex/gpsmid/england.osm.bz2 | bunzip2"

    def import_data(self):
        old_etag = get_osm_etag()

        request = AnyMethodRequest(self.ENGLAND_OSM_BZ2_URL, method='HEAD')
        response = urllib2.urlopen(request)
        new_etag = response.headers['ETag'][1:-1]

        if False and new_etag == old_etag:
            print 'OSM data not updated. Not updating.'
            return

        p = popen2.popen2(self.SHELL_CMD)

        parser = make_parser()
        parser.setContentHandler(OSMHandler(self._get_source(), self._get_entity_types(), self._find_types))
        parser.parse(p[0])

        set_osm_etag(new_etag)

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
            'atm':                 ('an', 'ATM',                      'ATMs',                      True,  False, ()),
            'bank':                ('a',  'bank',                     'banks',                     True,  True,  ()),
            'bench':               ('a',  'bench',                    'benches',                   True,  False, ()),
            'bar':                 ('a',  'bar',                      'bars',                      True,  True,  ()),
            'bicycle-parking':     ('a',  'bicycle rack',             'bicycle racks',             True,  False, ()),
            'cafe':                ('a',  'café',                     'cafés',                     False, False, ('food',)),
            'car-park':            ('a',  'car park',                 'car parks',                 False, False, ()),
            'cathedral':           ('a',  'cathedral',                'cathedrals',                False, False, ('place-of-worship',)),
            'chapel':              ('a',  'chapel',                   'chapels',                   False, False, ('place-of-worship',)),
            'church':              ('a',  'church',                   'churches',                  False, False, ('place-of-worship',)),
            'cinema':              ('a',  'cinema',                   'cinemas',                   True,  True,  ()),
            'cycle-shop':          ('a',  'cycle shop',               'cycle shops',               False, False, ('shop',)),
            'dispensing-pharmacy': ('a',  'dispensing pharmacy',      'dispensing pharmacies',     False, False, ('pharmacy',)),
            'doctors':             ('a',  "doctor's surgery",         "doctors' surgeries",        False, False, ('medical',)),
            'fast-food':           ('a',  'fast food outlet',         'fast food outlets',         False, False, ('food',)),
            'food':                ('a',  'place to eat',             'places to eat',             True,  True,  ()),
            'hospital':            ('a',  'hospital',                 'hospitals',                 False, False, ('medical',)),
            'ice-cream':           ('an', 'ice cream café',           'ice cream cafés',           False, False, ('cafe','food',)),
            'ice-rink':            ('an', 'ice rink',                 'ice rinks',                 False, False, ('sport',)),
            'library':             ('a',  'library',                  'libraries',                 True,  True,  ()),
            'mandir':              ('a',  'mandir',                   'mandirs',                   False, False, ('place-of-worship',)),
            'medical':             ('a',  'place relating to health', 'places relating to health', True,  True,  ()),
            'mosque':              ('a',  'mosque',                   'mosques',                   False, False, ('place-of-worship',)),
            'museum':              ('a',  'museum',                   'museums',                   False, False, ()),
            'car-park':            ('a',  'car park',                 'car parks',                 True,  False, ()),
            'park':                ('a',  'park',                     'parks',                     False, False, ()),
            'park-and-ride':       ('a',  'park and ride',            'park and rides',            False, False, ('car-park',)),
            'pharmacy':            ('a',  'pharmacy',                 'pharmacies',                False, False, ('medical',)),
            'place-of-worship':    ('a',  'place of worship',         'places of worship',         False, False, ()),
            'post-box':            ('a',  'post box',                 'post boxes',                True,  False, ()),
            'post-office':         ('a',  'post office',              'post offices',              True,  False, ()),
            'pub':                 ('a',  'pub',                      'pubs',                      True,  True,  ()),
            'public-library':      ('a',  'public library',           'public libraries',          True,  True,  ('library',)),
            'punt-hire':           ('a',  'place to hire punts',      'places to hire punts',      False, False, ()),
            'recycling':           ('a',  'recycling facility',       'recycling facilities',      True,  False, ()),
            'restaurant':          ('a',  'restaurant',               'restaurants',               False, False, ('food',)),
            'shop':                ('a',  'shop',                     'shops',                     False, False, ()),
            'sport':               ('a',  'place relating to sport',  'places relating to sport',  False, False, ()),
            'sports-centre':       ('a',  'sports centre',            'sports centres',            False, False, ('sport',)),
            'swimming-pool':       ('a',  'swimming pool',            'swimming pools',            False, False, ('sport',)),
            'synagogue':           ('a',  'synagogue',                'synagogues',                False, False, ('place-of-worship',)),
            'taxi-rank':           ('a',  'taxi rank',                'taxi ranks',                False, False, ()),
            'theatre':             ('a',  'theatre',                  'theatres',                  True,  True,  ()),
        }

        entity_types = {}
        new_entity_types = set()
        for slug, (article, verbose_name, verbose_name_plural, nearby, category, subtype_of) in ENTITY_TYPES.items():
            try:
                entity_type = EntityType.objects.get(slug=slug)
            except EntityType.DoesNotExist:
                entity_type = EntityType(
                    slug = slug,
                    verbose_name = verbose_name,
                    verbose_name_plural = verbose_name_plural,
                    article = article,
                    show_in_nearby_list = nearby,
                    show_in_category_list = category,
                )
                entity_type.save()
                new_entity_types.add(slug)
            entity_types[slug] = entity_type

        for slug in new_entity_types:
            subtype_of = ENTITY_TYPES[slug][5]
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

if __name__ == '__main__':
    provider = OSMMapsProvider()
    provider.import_data()
