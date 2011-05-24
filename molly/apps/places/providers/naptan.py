import ftplib
import os
import urllib
import zipfile
import tempfile
import random
import re
import csv
from collections import defaultdict
from StringIO import StringIO

from xml.sax import ContentHandler, make_parser
import yaml

from django.contrib.gis.geos import Point

from molly.apps.places.providers import BaseMapsProvider
from molly.apps.places.models import EntityType, Entity, EntityGroup, Source, EntityTypeCategory
from molly.conf.settings import batch

class NaptanContentHandler(ContentHandler):

    meta_names = {
        ('AtcoCode',): 'atco-code',
        ('NaptanCode',): 'naptan-code',
        ('PlateCode',): 'plate-code',
        ('Descriptor','CommonName'): 'common-name',
        ('Descriptor','Indicator'): 'indicator',
        ('Descriptor','Street'): 'street',
        ('Place','NptgLocalityRef'): 'locality-ref',
        ('Place','Location','Translation','Longitude'): 'longitude',
        ('Place','Location','Translation','Latitude'): 'latitude',
        ('AdministrativeAreaRef',): 'area',
        ('StopAreas', 'StopAreaRef'): 'stop-area',
        ('StopClassification', 'StopType'): 'stop-type',
        ('StopClassification', 'OffStreet', 'Rail', 'AnnotatedRailRef', 'CrsRef'): 'crs',
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
        elif name == 'StopArea':
            self.meta = defaultdict(str)

    def endElement(self, name):
        self.name_stack.pop()

        if name == 'StopPoint':
            try:
                # Classify metro stops according to their particular system
                if self.meta['stop-type'] == 'MET':
                    try:
                        entity_type = self.entity_types[self.meta['stop-type'] + ':' + self.meta['atco-code'][6:8]]
                    except KeyError:
                        entity_type = self.entity_types['MET']
                else:
                    entity_type = self.entity_types[self.meta['stop-type']]
            except KeyError:
                pass
            else:
                entity = self.add_stop(self.meta, entity_type, self.source)
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
            sa.title = self.meta['name']
            sa.save()

    def endDocument(self):
        pass

    def characters(self, text):
        top = tuple(self.name_stack[3:])

        try:
            self.meta[self.meta_names[top]] += text
        except KeyError:
            pass

    def add_stop(self, meta, entity_type, source):
        
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
          (indicator or '').lower() == 'not in use':
            # In the NaPTAN list, but indicates it's an unused stop
            return
        
        if self.meta['stop-type'] in ('MET','GAT','FER', 'RLY'):
            title = common_name
        else:
        
            # Convert indicator to a friendlier format
            indicator = {
                'opp': 'Opposite',
                'opposite': 'Opposite',
                'adj': 'Adjacent',
                'outside': 'Outside',
                'o/s': 'Outside',
                'nr': 'Near',
                'inside': 'Inside',
            }.get(indicator, indicator)
            
            if indicator is None and self.meta['stop-type'] in ('AIR', 'FTD', 'RSE', 'TMU', 'BCE'):
                indicator = 'Entrance to'
            
            if indicator is None and self.meta['stop-type'] in ('FBT',):
                indicator = 'Berth at'
            
            if indicator is None and self.meta['stop-type'] in ('RPL','PLT'):
                indicator = 'Platform at'
            
            title = ''
            
            if indicator != None:
                title += indicator + ' '
            
            title += common_name
            
            if street != None and street != '-' \
                         and not common_name.startswith(street):
                title += ', ' + street
            
            locality = self.nptg_localities.get(locality)
            if locality != None:
                title += ', ' + locality
        
        entity.title = title
        entity.primary_type = entity_type

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
        if indicator != None and re.match('Stop [A-Z]\d\d?', indicator):
            identifiers['stop'] = indicator[5:]
        
        
        entity.save(identifiers=identifiers)
        entity.all_types = (entity_type,)
        
        entity.update_all_types_completion()
        
        entity.groups.clear()
        for stop_area in self.stop_areas:
            sa, created = EntityGroup.objects.get_or_create(source=source, ref_code=stop_area)
            entity.groups.add(sa)
        
        return entity


class NaptanMapsProvider(BaseMapsProvider):

    HTTP_URL = "http://www.dft.gov.uk/NaPTAN/snapshot/NaPTANxml.zip"
    HTTP_CSV_URL = "http://www.dft.gov.uk/NaPTAN/snapshot/NaPTANcsv.zip"
    HTTP_NTPG_URL = "http://www.dft.gov.uk/nptg/snapshot/nptgcsv.zip"
    FTP_SERVER = 'journeyweb.org.uk'
    TRAIN_STATION = object()
    BUS_STOP_DEFINITION = {
            'slug': 'bus-stop',
            'article': 'a',
            'verbose-name': 'bus stop',
            'verbose-name-plural': 'bus stops',
            'nearby': True, 'category': False,
            'uri-local': 'BusStop',
        }
    TAXI_RANK_DEFINITION = {
        'slug': 'taxi-rank',
        'article': 'a',
        'verbose-name': 'taxi rank',
        'verbose-name-plural': 'taxi ranks',
        'nearby': False, 'category': False,
        'uri-local': 'TaxiRank',
    }
    RAIL_STATION_DEFINITION = {
            'slug': 'rail-station',
            'article': 'a',
            'verbose-name': 'rail station',
            'verbose-name-plural': 'rail stations',
            'nearby': True, 'category': False,
            'uri-local': 'RailStation',
        }
    HERITAGE_RAIL_STATION_DEFINITION = {
            'slug': 'heritage-rail-station',
            'article': 'a',
            'verbose-name': 'heritage rail station',
            'verbose-name-plural': 'heritage rail stations',
            'nearby': True, 'category': False,
            'uri-local': 'HeritageRailStation',
        }

    entity_type_definitions = {
        'BCT': BUS_STOP_DEFINITION,
        'BCS': BUS_STOP_DEFINITION,
        'BCQ': BUS_STOP_DEFINITION,
        'BSE': {
            'slug': 'bus-station-entrance',
            'article': 'a',
            'verbose-name': 'bus station entrance',
            'verbose-name-plural': 'bus station entrances',
            'nearby': False, 'category': False,
            'uri-local': 'BusStationEntrance',
        },
        'TXR': TAXI_RANK_DEFINITION,
        'STR': TAXI_RANK_DEFINITION,
        'RLY': RAIL_STATION_DEFINITION,
        'RSE': {
            'slug': 'rail-station-entrance',
            'article': 'a',
            'verbose-name': 'rail station entrance',
            'verbose-name-plural': 'rail station entrances',
            'nearby': False, 'category': False,
            'uri-local': 'RailStationEntrance',
        },
        'RPL': {
            'slug': 'rail-platform',
            'article': 'a',
            'verbose-name': 'rail platform',
            'verbose-name-plural': 'rail platform',
            'nearby': False, 'category': False,
            'uri-local': 'RailPlatform',
        },
        'TMU': {
            'slug': 'metro-entrance',
            'article': 'a',
            'verbose-name': 'metro entrance',
            'verbose-name-plural': 'metro entrances',
            'nearby': False, 'category': False,
            'uri-local': 'MetroEntrance',
        },
        'PLT': {
            'slug': 'platform',
            'article': 'a',
            'verbose-name': 'platform',
            'verbose-name-plural': 'platforms',
            'nearby': False, 'category': False,
            'uri-local': 'MetroPlatform',
        },
        'MET': {
            'slug': 'metro-station',
            'article': 'a',
            'verbose-name': 'metro station',
            'verbose-name-plural': 'metro stations',
            'nearby': True, 'category': False,
            'uri-local': 'MetroStation',
        },
        'MET:AV': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:BB': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:BF': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:BK': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:BL': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:BP': {
            'slug': 'tramway-stop',
            'article': 'a',
            'verbose-name': 'tramway stop',
            'verbose-name-plural': 'tramway stops',
            'nearby': True, 'category': False,
            'uri-local': 'TramwayStop',
        },
        'MET:BV': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:CA': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:CR': {
            'slug': 'tramlink-stop',
            'article': 'a',
            'verbose-name': 'tram stop',
            'verbose-name-plural': 'tram stops',
            'nearby': True, 'category': False,
            'uri-local': 'TramlinkStop',
        },
        'MET:CV': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:CW': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:DF': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:DL': {
            'slug': 'dlr-station',
            'article': 'a',
            'verbose-name': 'DLR station',
            'verbose-name-plural': 'DLR stations',
            'nearby': True, 'category': False,
            'uri-local': 'DLRStation',
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
            'article': 'a',
            'verbose-name': 'Subway station',
            'verbose-name-plural': 'Subway stations',
            'nearby': True, 'category': False,
            'uri-local': 'SubwayStation',
        },
        'MET:GO': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:GW': {
            'slug': 'shuttle-station',
            'article': 'a',
            'verbose-name': 'shuttle station',
            'verbose-name-plural': 'shuttle station',
            'nearby': True, 'category': False,
            'uri-local': 'ShuttleStation',
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
            'article': 'an',
            'verbose-name': 'Underground station',
            'verbose-name-plural': 'Underground stations',
            'nearby': True, 'category': False,
            'uri-local': 'TubeStation',
        },
        'MET:MA': {
            'slug': 'metrolink-station',
            'article': 'a',
            'verbose-name': 'Metrolink station',
            'verbose-name-plural': 'Metrolink stations',
            'nearby': True, 'category': False,
            'uri-local': 'MetrolinkStation',
        },
        'MET:MH': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:MN': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:NN': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:NO': {
            'slug': 'net-stop',
            'article': 'a',
            'verbose-name': 'tram stop',
            'verbose-name-plural': 'tram stops',
            'nearby': True, 'category': False,
            'uri-local': 'NETStop',
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
            'article': 'a',
            'verbose-name': 'Supertram stop',
            'verbose-name-plural': 'Supertram stops',
            'nearby': True, 'category': False,
            'uri-local': 'SupertramStop',
        },
        'MET:TL': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:TW': {
            'slug': 'tyne-and-wear-metro-station',
            'article': 'a',
            'verbose-name': 'Metro station',
            'verbose-name-plural': 'Metro stations',
            'nearby': True, 'category': False,
            'uri-local': 'TyneAndWearMetroStation',
        },
        'MET:TY': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:VR': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:WD': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:WH': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:WL': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:WM': {
            'slug': 'midland-metro-stop',
            'article': 'a',
            'verbose-name': 'Midland Metro stop',
            'verbose-name-plural': 'Midland Metro stops',
            'nearby': True, 'category': False,
            'uri-local': 'MidlandMetroStation',
        },
        'MET:WS': HERITAGE_RAIL_STATION_DEFINITION,
        'MET:WW': HERITAGE_RAIL_STATION_DEFINITION,
        'GAT': {
            'slug': 'airport',
            'article': 'an',
            'verbose-name': 'airport',
            'verbose-name-plural': 'airports',
            'nearby': True, 'category': False,
            'uri-local': 'Airport',
        },
        'AIR': {
            'slug': 'airport-entrance',
            'article': 'an',
            'verbose-name': 'airport entrance',
            'verbose-name-plural': 'airport entrances',
            'nearby': False, 'category': False,
            'uri-local': 'AirportEntrance',
        },
        'FER': {
            'slug': 'ferry-terminal',
            'article': 'a',
            'verbose-name': 'ferry terminal',
            'verbose-name-plural': 'ferry terminals',
            'nearby': True, 'category': False,
            'uri-local': 'FerryTerminal',
        },
        'FTD': {
            'slug': 'ferry-terminal-entrance',
            'article': 'a',
            'verbose-name': 'ferry terminal entrance',
            'verbose-name-plural': 'ferry terminal entrances',
            'nearby': False, 'category': False,
            'uri-local': 'FerryTerminalEntrance',
        },
        'FBT': {
            'slug': 'ferry-berth',
            'article': 'a',
            'verbose-name': 'ferry berth',
            'verbose-name-plural': 'ferry berths',
            'nearby': False, 'category': False,
            'uri-local': 'FerryBerth',
        },
        None: {
            'slug': 'public-transport-access-node',
            'article': 'a',
            'verbose-name': 'public transport access node',
            'verbose-name-plural': 'public transport access nodes',
            'nearby': False, 'category': False,
            'uri-local': 'PublicTransportAccessNode',
        }
    }


    def __init__(self, method, areas=None, username=None, password=None):
        self._username, self._password = username, password
        self._method = method
        
        # Add 910 because we always want to import railway stations
        if areas is not None:
            areas += ('910',)
        self._areas = areas

    @batch('%d 10 * * mon' % random.randint(0, 59))
    def import_data(self, metadata, output):
        method, username, password = self._method, self._username, self._password
        if not method in ('http', 'ftp',):
            raise ValueError("mode must be either 'http' or 'ftp'")
        if (method == 'ftp') == (username is None or password is None):
            raise ValueError("username and password must be provided iff mode is 'ftp'")

        self._source = self._get_source()
        self._entity_types = self._get_entity_types()

        if self._method == 'http':
            self._import_from_http()
        elif self._method == 'ftp':
            self._import_from_ftp()
        
        return metadata
    
    def _connect_to_ftp(self):
        return ftplib.FTP(self.FTP_SERVER,
            self._username,
            self._password,
        )
    
    def _import_from_ftp(self):
        def data_chomper(f):
            def chomp(data):
                os.write(f, data)
            return chomp

        ftp = self._connect_to_ftp()
        
        files = {}
        
        # Get NPTG localities
        f, filename =  tempfile.mkstemp()
        ftp.cwd("/V2/NPTG/")
        ftp.retrbinary('RETR nptgcsv.zip', data_chomper(f))
        os.close(f)
        archive = zipfile.ZipFile(filename)
        if hasattr(archive, 'open'):
            f = archive.open('Localities.csv')
        else:
            f = StringIO(archive.read('Localities.csv'))
        localities = self._get_nptg(f)
        os.unlink(filename)
        
        if self._areas is None:
            f, filename = tempfile.mkstemp()
            
            try:
                ftp.cwd("/V2/complete/")
                ftp.retrbinary('RETR NaPTAN.xml', data_chomper(f))
            except ftplib.error_temp:
                ftp = self._connect_to_ftp()
                ftp.cwd("/V2/complete/")
                ftp.retrbinary('RETR NaPTAN.xml', data_chomper(f))
            
            ftp.quit()
            os.close(f)
            
            f = open(filename)
            self._import_from_pipe(f, localities)
            os.unlink(filename)
            
        else:
            for area in self._areas:
                f, filename = tempfile.mkstemp()
                files[area] = filename
            
                try:
                    ftp.cwd("/V2/%s/" % area)
                    ftp.retrbinary('RETR NaPTAN%sxml.zip' % area, data_chomper(f))
                except ftplib.error_temp:
                    ftp = self._connect_to_ftp()
                    ftp.cwd("/V2/%s/" % area)
                    ftp.retrbinary('RETR NaPTAN%sxml.zip' % area, data_chomper(f))
                os.close(f)
            
            try:
                ftp.quit()
            except ftplib.error_temp:
                pass
            
            for (area, filename) in files.items():
                archive = zipfile.ZipFile(filename)
                if hasattr(archive, 'open'):
                    f = archive.open('NaPTAN%d.xml' % int(area))
                else:
                    f = StringIO(archive.read('NaPTAN%d.xml' % int(area)))
                self._import_from_pipe(f, localities)
                archive.close()
                os.unlink(filename)

    def _import_from_http(self):
        
        # Get NPTG localities
        f, filename =  tempfile.mkstemp()
        os.close(f)
        urllib.urlretrieve(self.HTTP_NTPG_URL, filename)
        archive = zipfile.ZipFile(filename)
        if hasattr(archive, 'open'):
            f = archive.open('Localities.csv')
        else:
            f = StringIO(archive.read('Localities.csv'))
        localities = self._get_nptg(f)
        os.unlink(filename)
        
        f, filename = tempfile.mkstemp()
        os.close(f)
        urllib.urlretrieve(self.HTTP_URL, filename)
        archive = zipfile.ZipFile(filename)
        if hasattr(archive, 'open'):
            f = archive.open('NaPTAN.xml')
        else:
            f = StringIO(archive.read('NaPTAN.xml'))
        self._import_from_pipe(f, localities, areas=self._areas)
        archive.close()
        os.unlink(filename)

    def _import_from_pipe(self, pipe_r, localities, areas=None):
        parser = make_parser()
        parser.setContentHandler(NaptanContentHandler(self._entity_types, self._source, localities, areas))
        parser.parse(pipe_r)

    def _get_nptg(self, f):
        localities = {}
        csvfile = csv.reader(f)
        csvfile.next()
        for line in csvfile:
            localities[line[0]] = line[1]
        return localities

    def _get_entity_types(self):

        entity_types = {}
        category, created = EntityTypeCategory.objects.get_or_create(name='Transport')
        for stop_type in self.entity_type_definitions:
            et = self.entity_type_definitions[stop_type]
            
            try:
                entity_type = EntityType.objects.get(slug=et['slug'])
            except EntityType.DoesNotExist:
                entity_type = EntityType(slug=et['slug'])
            
            entity_type.category = category
            entity_type.uri = "http://mollyproject.org/schema/maps#%s" % et['uri-local']
            entity_type.article = et['article']
            entity_type.verbose_name = et['verbose-name']
            entity_type.verbose_name_plural = et['verbose-name-plural']
            if created:
                entity_type.show_in_nearby_list = et['nearby']
                entity_type.show_in_category_list = et['category']
            entity_type.save()

            entity_types[stop_type] = entity_type

        for stop_type, entity_type in entity_types.items():
            if entity_type.slug == 'public-transport-access-node':
                continue
            entity_type.subtype_of.add(entity_types[None])
            if stop_type.startswith('MET') and stop_type != 'MET' and entity_type.slug != self.RAIL_STATION_DEFINITION['slug']:
                entity_type.subtype_of.add(entity_types['MET'])
        

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
        p.import_data(None, None)
