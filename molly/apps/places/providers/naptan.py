import ftplib
import os
import urllib
import zipfile
import tempfile
import random
import re
import csv
from warnings import warn
from collections import defaultdict
from datetime import timedelta
try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

from xml.sax import ContentHandler, make_parser
import yaml

from django.db import transaction
from django.conf import settings
from django.contrib.gis.geos import Point
from django.utils.translation import ugettext_noop as _
from django.utils.translation import ugettext, get_language

from molly.apps.places.providers import BaseMapsProvider
from molly.apps.places.models import EntityType, Entity, EntityGroup, Source, EntityTypeCategory
from molly.conf.provider import task
from molly.utils.i18n import override, set_name_in_language

class NaptanContentHandler(ContentHandler):

    meta_names = {
        ('AtcoCode',): 'atco-code',
        ('NaptanCode',): 'naptan-code',
        ('PlateCode',): 'plate-code',
        ('Descriptor','CommonName'): 'common-name',
        ('AlternativeDescriptors', 'Descriptor','CommonName'): 'common-name',
        ('Descriptor','Indicator'): 'indicator',
        ('Descriptor','Street'): 'street',
        ('Place','NptgLocalityRef'): 'locality-ref',
        ('Place','Location','Translation','Longitude'): 'longitude',
        ('Place','Location','Translation','Latitude'): 'latitude',
        ('AdministrativeAreaRef',): 'area',
        ('StopAreas', 'StopAreaRef'): 'stop-area',
        ('StopClassification', 'StopType'): 'stop-type',
        ('StopClassification', 'OffStreet', 'Rail', 'AnnotatedRailRef', 'CrsRef'): 'crs',
        ('StopClassification', 'OffStreet', 'Rail', 'AnnotatedRailRef', 'TiplocRef'): 'tiploc',
        ('StopAreaCode',): 'area-code',
        ('Name',): 'name',
    }

    @staticmethod
    def naptan_dial(c):
        """
        Convert a alphabetical NaPTAN code in the database to the numerical code
        used on bus stops
        """
        if c.isdigit():
            return c
        return unicode(min(9, (ord(c)-91)//3))

    def __init__(self, entity_types, source, nptg_localities = None, areas=None):
        self.name_stack = []
        self.entity_types, self.source = entity_types, source
        self.entities = set()
        self.nptg_localities = {} if nptg_localities is None else nptg_localities
        self.areas = areas
        with open(os.path.join(os.path.dirname(__file__), '..', 'data', 'tube-references.yaml')) as fd:
            self.tube_references = yaml.load(fd)

    def startElement(self, name, attrs):
        self.name_stack.append(name)

        if name == 'StopPoint':
            self.stop_areas = []
            self.meta = defaultdict(str)
            self.names = dict()
        elif name == 'StopArea':
            self.meta = defaultdict(str)
            self.names = dict()
        elif name in ('CommonName', 'Name'):
            if 'xml:lang' in attrs:
                self.lang = attrs['xml:lang'].lower()
            else:
                self.lang = None
    
    def endElement(self, name):
        self.name_stack.pop()

        if name == 'StopPoint':
            try:
                # Classify metro stops according to their particular system
                if self.meta['stop-type'] == 'MET':
                    try:
                        entity_type, is_entrance = self.entity_types[self.meta['stop-type'] + ':' + self.meta['atco-code'][6:8]]
                    except KeyError:
                        entity_type, is_entrance = self.entity_types['MET']
                else:
                    entity_type, is_entrance = self.entity_types[self.meta['stop-type']]
            except KeyError:
                pass
            else:
                entity = self.add_stop(self.meta, entity_type, self.source, is_entrance)
                if entity:
                    self.entities.add(entity)
        
        elif name == 'StopAreaRef':
            self.stop_areas.append(self.meta['stop-area'])
            del self.meta['stop-area']
        
        elif name == 'StopArea':
            if self.areas != None:
                in_area = False
                for area in self.areas:
                    if self.meta['area-code'].startswith(area):
                        in_area = True
                if not in_area:
                    return
            
            sa, created = EntityGroup.objects.get_or_create(
                source=self.source,
                ref_code=self.meta['area-code'])
            sa.save()
            for lang_code, name in self.names.items():
                if lang_code is None: lang_code = 'en'
                set_name_in_language(sa, lang_code, title=name)
        
        elif name == 'CommonName':
            if self.lang not in self.names:
                self.names[self.lang] = self.meta['common-name']
        
        elif name == 'Name' and self.meta['name'] != '':
            if self.lang not in self.names:
                self.names[self.lang] = self.meta['name']

    def endDocument(self):
        # Delete all entities which have been deleted in the NaPTAN
        Entity.objects.filter(source=self.source).exclude(id__in=(e.id for e in self.entities)).delete()

    def characters(self, text):
        top = tuple(self.name_stack[3:])

        try:
            self.meta[self.meta_names[top]] += text
        except KeyError:
            pass

    def add_stop(self, meta, entity_type, source, is_entrance):
        
        # Check this entity is in an area
        if self.areas != None:
            in_area = False
            for area in self.areas:
                if meta['atco-code'].startswith(area):
                    in_area = True
            if not in_area:
                return
        
        # See if we're updating an existing object, or creating a new one
        try:
            entity = Entity.objects.get(source=source,
                                        _identifiers__scheme='atco',
                                        _identifiers__value=meta['atco-code'])
        except Entity.DoesNotExist:
            entity = Entity(source=source)
        except Entity.MultipleObjectsReturned:
            # Handle clashes
            Entity.objects.filter(source=source,
                                 _identifiers__scheme='atco',
                                 _identifiers__value=meta['atco-code']).delete()
            entity = Entity(source=source)
        
        common_name, indicator, locality, street = [meta.get(k) for k in
                    ('common-name', 'indicator', 'locality-ref', 'street')]
        
        if (common_name or '').endswith(' DEL') or \
           (indicator or '').lower() == 'not in use' or \
           'to define route' in (common_name or '') or \
           'to def rte' in (common_name or '') or \
           'to def route' in (common_name or '') or \
           'def.rte' in (common_name or ''):
            # In the NaPTAN list, but indicates it's an unused stop
            return
        
        if self.meta['stop-type'] in ('MET','GAT','FER', 'RLY'):
            names = self.names
        else:
            
            names = dict()
            
            for lang_code, lang_name in settings.LANGUAGES:
                with override(lang_code):
                    
                    # Try and find one in our preferred order
                    for lang in (lang_code, 'en', None):
                        if lang in self.names:
                            common_name = self.names[lang]
                            break
                
                    # Expand abbreviations in indicators
                    if indicator is not None:
                        parts = []
                        for part in indicator.split():
                            parts.append({
                                # Translators: This is referring to bus stop location descriptions
                                'op': ugettext('Opposite'),
                                'opp': ugettext('Opposite'),
                                'opposite': ugettext('Opposite'),
                                # Translators: This is referring to bus stop location descriptions
                                'adj': ugettext('Adjacent'),
                                # Translators: This is referring to bus stop location descriptions
                                'outside': ugettext('Outside'),
                                'o/s': ugettext('Outside'),
                                # Translators: This is referring to bus stop location descriptions
                                'nr': ugettext('Near'),
                                # Translators: This is referring to bus stop location descriptions
                                'inside': ugettext('Inside'),
                                # Translators: This is referring to bus stop location descriptions
                                'stp': ugettext('Stop'),
                            }.get(part.lower(), part))
                        indicator = ' '.join(parts)
                    
                    if indicator is None and self.meta['stop-type'] in ('AIR', 'FTD', 'RSE', 'TMU', 'BCE'):
                        # Translators: This is referring to public transport entities
                        title = ugettext('Entrance to %s') % common_name
                    
                    elif indicator is None and self.meta['stop-type'] in ('FBT',):
                        # Translators: This is referring to ferry ports
                        title = ugettext('Berth at %s') % common_name
                    
                    elif indicator is None and self.meta['stop-type'] in ('RPL','PLT'):
                        # Translators: This is referring to rail and metro stations
                        title = ugettext('Platform at %s') % common_name
                    
                    elif indicator is not None and indicator.lower() != 'none' \
                        and indicator not in common_name:
                        title = indicator + ' ' + common_name
                    
                    else:
                        title = common_name
                    
                    if street not in (None, '-', '---'):
                        # Deal with all-caps street names
                        if street.upper() == street:
                            fixedstreet = ''
                            wordstart = True
                            for letter in street:
                                if wordstart:
                                    wordstart = False
                                    fixedstreet += letter
                                    continue
                                elif letter == ' ':
                                    wordstart = True
                                    fixedstreet += letter
                                    continue
                                else:
                                    fixedstreet += letter.lower()
                            street = fixedstreet
                        
                        if street not in title:
                            title += ', ' + street
                    
                    locality_lang = self.nptg_localities.get(locality)
                    if locality_lang != None:
                        for lang in (lang_code, 'en', 'cy'):
                            if lang in locality_lang:
                                if locality_lang[lang] != street:
                                    title += ', ' + locality_lang[lang]
                                break
                    
                    names[lang_code] = title
        
        entity.primary_type = entity_type
        entity.is_entrance = is_entrance
        
        if not entity.metadata:
            entity.metadata = {}
        entity.metadata['naptan'] = meta
        entity.location = Point(float(meta['longitude']), float(meta['latitude']), srid=4326)
        entity.geometry = entity.location
        
        if meta['atco-code'] in self.tube_references:
            entity.metadata['london-underground-identifiers'] = self.tube_references[meta['atco-code']]
        
        identifiers = {
            'atco': meta['atco-code'],
        }
        if 'naptan-code' in meta:
            meta['naptan-code'] = ''.join(map(self.naptan_dial, meta['naptan-code']))
            identifiers['naptan'] = meta['naptan-code']
        if 'plate-code' in meta:
            identifiers['plate'] = meta['plate-code']
        if 'crs' in meta:
            identifiers['crs'] = meta['crs']
        if 'tiploc' in meta:
            identifiers['tiploc'] = meta['tiploc']
        if indicator != None and re.match('Stop [A-Z]\d\d?', indicator):
            identifiers['stop'] = indicator[5:]
        
        entity.save(identifiers=identifiers)
        
        for lang_code, name in names.items():
            # This is the NaPTAN, so default to English
            if lang_code is None: lang_code = 'en'
            set_name_in_language(entity, lang_code, title=name)
        
        entity.all_types = (entity_type,)
        entity.update_all_types_completion()
        entity.groups.clear()
        for stop_area in self.stop_areas:
            sa, created = EntityGroup.objects.get_or_create(source=source, ref_code=stop_area)
            entity.groups.add(sa)
        entity.save()
        
        return entity


class NaptanMapsProvider(BaseMapsProvider):

    HTTP_URL = "http://www.dft.gov.uk/NaPTAN/snapshot/NaPTANxml.zip"
    HTTP_CSV_URL = "http://www.dft.gov.uk/NaPTAN/snapshot/NaPTANcsv.zip"
    HTTP_NTPG_URL = "http://www.dft.gov.uk/nptg/snapshot/nptgcsv.zip"
    FTP_SERVER = 'journeyweb.org.uk'
    TRAIN_STATION = object()
    BUS_STOP_DEFINITION = {
            'slug': 'bus-stop',
            'verbose-name': _('bus stop'),
            'verbose-name-singular': _('a bus stop'),
            'verbose-name-plural': _('bus stops'),
            'nearby': True, 'category': False,
            'uri-local': 'BusStop',
            'is-entrance': False,
        }
    TAXI_RANK_DEFINITION = {
        'slug': 'taxi-rank',
        'verbose-name': _('taxi rank'),
        'verbose-name-singular': _('a taxi rank'),
        'verbose-name-plural': _('taxi ranks'),
        'nearby': False, 'category': False,
        'uri-local': 'TaxiRank',
            'is-entrance': False,
    }
    RAIL_STATION_DEFINITION = {
            'slug': 'rail-station',
            'verbose-name': _('rail station'),
            'verbose-name-singular': _('a rail station'),
            'verbose-name-plural': _('rail stations'),
            'nearby': True, 'category': False,
            'uri-local': 'RailStation',
            'is-entrance': False,
        }
    HERITAGE_RAIL_STATION_DEFINITION = {
            'slug': 'heritage-rail-station',
            'verbose-name': _('heritage rail station'),
            'verbose-name-singular': _('a heritage rail station'),
            'verbose-name-plural': _('heritage rail stations'),
            'nearby': True, 'category': False,
            'uri-local': 'HeritageRailStation',
            'is-entrance': False,
        }

    entity_type_definitions = {
        'BCT': BUS_STOP_DEFINITION,
        'BCS': BUS_STOP_DEFINITION,
        'BCQ': BUS_STOP_DEFINITION,
        'BSE': {
            'slug': 'bus-station-entrance',
            'verbose-name': _('bus station entrance'),
            'verbose-name-singular': _('a bus station entrance'),
            'verbose-name-plural': _('bus station entrances'),
            'nearby': False, 'category': False,
            'uri-local': 'BusStationEntrance',
            'is-entrance': True,
        },
        'TXR': TAXI_RANK_DEFINITION,
        'STR': TAXI_RANK_DEFINITION,
        'RLY': RAIL_STATION_DEFINITION,
        'RSE': {
            'slug': 'rail-station-entrance',
            'verbose-name': _('rail station entrance'),
            'verbose-name-singular': _('a rail station entrance'),
            'verbose-name-plural': _('rail station entrances'),
            'nearby': False, 'category': False,
            'uri-local': 'RailStationEntrance',
            'is-entrance': True,
        },
        'RPL': {
            'slug': 'rail-platform',
            'verbose-name': _('rail platform'),
            'verbose-name-singular': _('a rail platform'),
            'verbose-name-plural': _('rail platforms'),
            'nearby': False, 'category': False,
            'uri-local': 'RailPlatform',
            'is-entrance': False,
        },
        'TMU': {
            'slug': 'metro-entrance',
            # Translators: This is the generic term for rapid transit systems
            'verbose-name': _('metro station entrance'),
            # Translators: This is the generic term for rapid transit systems
            'verbose-name-singular': _('a metro station entrance'),
            # Translators: This is the generic term for rapid transit systems
            'verbose-name-plural': _('metro station entrances'),
            'nearby': False, 'category': False,
            'uri-local': 'MetroEntrance',
            'is-entrance': True,
        },
        'PLT': {
            'slug': 'platform',
            # Translators: This is the generic term for rapid transit systems
            'verbose-name': _('metro station platform'),
            # Translators: This is the generic term for rapid transit systems
            'verbose-name-singular': _('a metro station platform'),
            # Translators: This is the generic term for rapid transit systems
            'verbose-name-plural': _('metro station platforms'),
            'nearby': False, 'category': False,
            'uri-local': 'MetroPlatform',
            'is-entrance': False,
        },
        'MET': {
            'slug': 'metro-station',
            # Translators: This is the generic term for rapid transit systems
            'verbose-name': _('metro station'),
            # Translators: This is the generic term for rapid transit systems
            'verbose-name-singular': _('a metro station'),
            # Translators: This is the generic term for rapid transit systems
            'verbose-name-plural': _('metro stations'),
            'nearby': False, 'category': False,
            'uri-local': 'MetroStation',
            'is-entrance': False,
        },
        'MET:AV': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:BB': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:BF': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:BK': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:BL': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:BP': {
            'slug': 'tramway-stop',
            # Translators: This is the Blackpool tram system
            'verbose-name': _('tramway stop'),
            # Translators: This is the Blackpool tram system
            'verbose-name-singular': _('a tramway stop'),
            # Translators: This is the Blackpool tram system
            'verbose-name-plural': _('tramway stops'),
            'nearby': True, 'category': False,
            'uri-local': 'TramwayStop',
            'is-entrance': False,
        },
        'MET:BV': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:CA': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:CR': {
            'slug': 'tramlink-stop',
            'verbose-name': _('tram stop'),
            'verbose-name-singular': _('a tram stop'),
            'verbose-name-plural': _('tram stops'),
            'nearby': True, 'category': False,
            'uri-local': 'TramlinkStop',
            'is-entrance': False,
        },
        'MET:CV': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:CW': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:DF': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:DL': {
            'slug': 'dlr-station',
            # Translators: This is the Docklands Light Railway
            'verbose-name': _('DLR station'),
            # Translators: This is the Docklands Light Railway
            'verbose-name-singular': _('a DLR station'),
            # Translators: This is the Docklands Light Railway
            'verbose-name-plural': _('DLR stations'),
            'nearby': True, 'category': False,
            'uri-local': 'DLRStation',
            'is-entrance': False,
        },
        'MET:DM': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:EB': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:EK': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:EL': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:EV': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:FB': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:FF': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:GC': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:GL': {
            'slug': 'subway-station',
            # Translators: This is the Glasgow Subway
            'verbose-name': _('Subway station'),
            # Translators: This is the Glasgow Subway
            'verbose-name-singular': _('a Subway station'),
            # Translators: This is the Glasgow Subway
            'verbose-name-plural': _('Subway stations'),
            'nearby': True, 'category': False,
            'uri-local': 'SubwayStation',
            'is-entrance': False,
        },
        'MET:GO': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:GW': {
            'slug': 'shuttle-station',
            # Translators: This is the Gatwick airport shuttle
            'verbose-name': _('shuttle station'),
            # Translators: This is the Gatwick airport shuttle
            'verbose-name-singular': _('a shuttle station'),
            # Translators: This is the Gatwick airport shuttle
            'verbose-name-plural': _('shuttle stations'),
            'nearby': True, 'category': False,
            'uri-local': 'ShuttleStation',
            'is-entrance': False,
        },
        'MET:GR': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:IW': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:KD': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:KE': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:KW': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:LH': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:LL': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:LU': {
            'slug': 'tube-station',
            # Translators: This is the London Underground (Tube)
            'verbose-name': _('Underground station'),
            # Translators: This is the London Underground (Tube)
            'verbose-name-singular': _('an Underground station'),
            # Translators: This is the London Underground (Tube)
            'verbose-name-plural': _('Underground stations'),
            'nearby': True, 'category': False,
            'uri-local': 'TubeStation',
            'is-entrance': False,
        },
        'MET:MA': {
            'slug': 'metrolink-station',
            # Translators: This is the Manchester tram system
            'verbose-name': _('Metrolink station'),
            # Translators: This is the Manchester tram system
            'verbose-name-singular': _('a Metrolink station'),
            # Translators: This is the Manchester tram system
            'verbose-name-plural': _('Metrolink stations'),
            'nearby': True, 'category': False,
            'uri-local': 'MetrolinkStation',
            'is-entrance': False,
        },
        'MET:MH': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:MN': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:NN': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:NO': {
            'slug': 'net-stop',
            'verbose-name': _('tram stop'),
            'verbose-name-singular': _('a tram stop'),
            'verbose-name-plural': _('tram stops'),
            'nearby': True, 'category': False,
            'uri-local': 'NETStop',
            'is-entrance': False,
        },
        'MET:NV': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:NY': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:PD': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:PR': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:RE': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:RH': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:SD': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:SL': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:SM': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:SP': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:SR': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:ST': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:SV': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:SY': {
            'slug': 'supertram-stop',
            # Translators: This is the Sheffield tram system
            'verbose-name': _('Supertram stop'),
            # Translators: This is the Sheffield tram system
            'verbose-name-singular': _('a Supertram stop'),
            # Translators: This is the Sheffield tram system
            'verbose-name-plural': _('Supertram stops'),
            'nearby': True, 'category': False,
            'uri-local': 'SupertramStop',
            'is-entrance': False,
        },
        'MET:TL': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:TW': {
            'slug': 'tyne-and-wear-metro-station',
            # Translators: This is the Tyne & Wear metro system
            'verbose-name': _('Metro station'),
            # Translators: This is the Tyne & Wear metro system
            'verbose-name-singular': _('a Metro station'),
            # Translators: This is the Tyne & Wear metro system
            'verbose-name-plural': _('Metro stations'),
            'nearby': True, 'category': False,
            'uri-local': 'TyneAndWearMetroStation',
            'is-entrance': False,
        },
        'MET:TY': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:VR': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:WD': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:WH': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:WL': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:WM': {
            'slug': 'midland-metro-stop',
            # Translators: This is the Midland Metro system
            'verbose-name': _('Midland Metro stop'),
            # Translators: This is the Midland Metro system
            'verbose-name-singular': _('a Midland Metro stop'),
            # Translators: This is the Midland Metro system
            'verbose-name-plural': _('Midland Metro stops'),
            'nearby': True, 'category': False,
            'uri-local': 'MidlandMetroStation',
            'is-entrance': False,
        },
        'MET:WS': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:WW': HERITAGE_RAIL_STATION_DEFINITION,
        'GAT': {
            'slug': 'airport',
            'verbose-name': _('airport'),
            'verbose-name-singular': _('an airport'),
            'verbose-name-plural': _('airports'),
            'nearby': True, 'category': False,
            'uri-local': 'Airport',
            'is-entrance': False,
        },
        'AIR': {
            'slug': 'airport-entrance',
            'verbose-name': _('airport entrance'),
            'verbose-name-singular': _('an airport entrance'),
            'verbose-name-plural': _('airport entrances'),
            'nearby': False, 'category': False,
            'uri-local': 'AirportEntrance',
            'is-entrance': True,
        },
        'FER': {
            'slug': 'ferry-terminal',
            'verbose-name': _('ferry terminal'),
            'verbose-name-singular': _('a ferry terminal'),
            'verbose-name-plural': _('ferry terminals'),
            'nearby': True, 'category': False,
            'uri-local': 'FerryTerminal',
            'is-entrance': False,
        },
        'FTD': {
            'slug': 'ferry-terminal-entrance',
            'verbose-name': _('ferry terminal entrance'),
            'verbose-name-singular': _('a ferry terminal entrance'),
            'verbose-name-plural': _('ferry terminal entrances'),
            'nearby': False, 'category': False,
            'uri-local': 'FerryTerminalEntrance',
            'is-entrance': True,
        },
        'FBT': {
            'slug': 'ferry-berth',
            'verbose-name': _('ferry berth'),
            'verbose-name-singular': _('a ferry berth'),
            'verbose-name-plural': _('ferry berths'),
            'nearby': False, 'category': False,
            'uri-local': 'FerryBerth',
            'is-entrance': False,
        },
        None: {
            'slug': 'public-transport-access-node',
            'verbose-name': _('public transport access node'),
            'verbose-name-singular': _('a public transport access node'),
            'verbose-name-plural': _('public transport access nodes'),
            'nearby': False, 'category': False,
            'uri-local': 'PublicTransportAccessNode',
            'is-entrance': False,
        }
    }


    def __init__(self, method=None, areas=None, username=None, password=None):
        self._username, self._password = username, password
        self._method = method
        if self._method:
            warn('method is deprecated, only HTTP is now supported', DeprecationWarning)
        
        # Add 910 because we always want to import railway stations
        if areas is not None:
            areas += ('910',)
        self._areas = areas

    @task(run_every=timedelta(days=7))
    def import_data(self, **metadata):
        username, password = self._username, self._password

        self._source = self._get_source()
        self._entity_types = self._get_entity_types()
        
        # Get NPTG localities
        archive = zipfile.ZipFile(StringIO(urllib.urlopen(self.HTTP_NTPG_URL).read()))
        f = StringIO(archive.read('Localities.csv'))
        falt = StringIO(archive.read('LocalityAlternativeNames.csv'))
        localities = self._get_nptg_alt_names(falt, self._get_nptg(f))
        
        with tempfile.TemporaryFile() as temp:
            temp.write(urllib.urlopen(self.HTTP_URL).read())
            archive = zipfile.ZipFile(temp)
            if hasattr(archive, 'open'):
                f = archive.open('NaPTAN.xml')
            else:
                f = StringIO(archive.read('NaPTAN.xml'))
            self._import_from_pipe(f, localities, areas=self._areas)
            archive.close()

    @transaction.commit_on_success
    def _import_from_pipe(self, pipe_r, localities, areas=None):
        parser = make_parser()
        parser.setContentHandler(NaptanContentHandler(self._entity_types, self._source, localities, areas))
        parser.parse(pipe_r)

    def _get_nptg(self, f):
        localities=defaultdict(dict)
        csvfile = csv.reader(f)
        csvfile.next()
        for line in csvfile:
            if line[2].lower() not in localities[line[0]]:
                localities[line[0]][line[2].lower()] = line[1]
        return localities

    def _get_nptg_alt_names(self, f, localities):
        csvfile = csv.reader(f)
        csvfile.next()
        for line in csvfile:
            if line[3].lower() not in localities[line[0]]:
                localities[line[0]][line[3].lower()] = line[2]
        return localities

    def _get_entity_types(self):

        entity_types = {}
        category, created = EntityTypeCategory.objects.get_or_create(name=_('Transport'))
        category.save()
        
        for stop_type in self.entity_type_definitions:
            et = self.entity_type_definitions[stop_type]
            
            try:
                entity_type = EntityType.objects.get(slug=et['slug'])
            except EntityType.DoesNotExist:
                entity_type = EntityType(slug=et['slug'])
            
            entity_type.category = category
            entity_type.uri = "http://mollyproject.org/schema/maps#%s" % et['uri-local']
            if created:
                entity_type.show_in_nearby_list = et['nearby']
                entity_type.show_in_category_list = et['category']
            entity_type.save()
            for lang_code, lang_name in settings.LANGUAGES:
                with override(lang_code):
                    set_name_in_language(entity_type, lang_code,
                                         verbose_name=ugettext(et['verbose-name']),
                                         verbose_name_singular=ugettext(et['verbose-name-singular']),
                                         verbose_name_plural=ugettext(et['verbose-name-plural']))
            
            entity_types[stop_type] = (entity_type, et['is-entrance'])

        for stop_type, (entity_type, is_entrance) in entity_types.items():
            if entity_type.slug == 'public-transport-access-node':
                continue
            entity_type.subtype_of.add(entity_types[None][0])
            if stop_type.startswith('MET') and stop_type != 'MET' and entity_type.slug != self.RAIL_STATION_DEFINITION['slug']:
                entity_type.subtype_of.add(entity_types['MET'][0])
        
        return entity_types

    def _get_source(self):
        try:
            source = Source.objects.get(module_name="molly.providers.apps.maps.naptan")
        except Source.DoesNotExist:
            source = Source(module_name="molly.providers.apps.maps.naptan")

        source.name = "National Public Transport Access Nodes (NaPTAN) database"
        source.save()

        return source

try:
    from secrets import SECRETS
except ImportError:
    pass
else:
    if __name__ == '__main__':
        p = NaptanMapsProvider(method='ftp', username=SECRETS.journeyweb[0], password=SECRETS.journeyweb[1], areas=('340',))
        p.import_data()
