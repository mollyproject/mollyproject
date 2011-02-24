import ftplib, os, urllib, zipfile, tempfile, random, re, csv

from collections import defaultdict
from StringIO import StringIO

from xml.sax import ContentHandler, make_parser

from django.contrib.gis.geos import Point

from molly.apps.places.providers import BaseMapsProvider
from molly.apps.places.models import EntityType, Entity, Source
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
        ('StopClassification', 'StopType'): 'stop-type',
    }

    @staticmethod
    def naptan_dial(c):
        """
        Convert a alphabetical NaPTAN code in the database to the numerical code
        used on bus stops
        """
        return unicode(min(9, (ord(c)-91)//3))

    def __init__(self, entity_types, source, nptg_localities = None, areas=None):
        self.name_stack = []
        self.entity_types, self.source = entity_types, source
        self.entities = set()
        self.nptg_localities = {} if nptg_localities is None else nptg_localities
        self.areas = areas

    def startElement(self, name, attrs):
        self.name_stack.append(name)

        if name == 'StopPoint':
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
        
        if self.meta['stop-type'] in ('MET','GAT','FER'):
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

        identifiers = {
            'atco': meta['atco-code'],
        }
        if 'naptan-code' in meta:
            meta['naptan-code'] = ''.join(map(self.naptan_dial, meta['naptan-code']))
            identifiers['naptan'] = meta['naptan-code']
        if 'plate-code' in meta:
            identifiers['plate'] = meta['plate-code']
        if indicator != None and re.match('Stop [A-Z]\d\d?', indicator):
            identifiers['stop'] = indicator[5:]

        entity.save(identifiers=identifiers)
        entity.all_types.add(entity_type)
        
        entity.update_all_types_completion()

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

    entity_type_definitions = {
        'BCT': BUS_STOP_DEFINITION,
        'BCS': BUS_STOP_DEFINITION,
        'BCQ': BUS_STOP_DEFINITION,
        'TXR': TAXI_RANK_DEFINITION,
        'STR': TAXI_RANK_DEFINITION,
        TRAIN_STATION: { # We want to add this as an entity_type, but not have it match when parsing the main naptan file
            'slug': 'rail-station',
            'article': 'a',
            'verbose-name': 'rail station',
            'verbose-name-plural': 'rail stations',
            'nearby': True, 'category': False,
            'uri-local': 'RailStation',
        },
        'MET': {
            'slug': 'metro-station',
            'article': 'a',
            'verbose-name': 'metro station',
            'verbose-name-plural': 'metro stations',
            'nearby': True, 'category': False,
            'uri-local': 'MetroStation',
        },
        'MET:CR': {
            'slug': 'tramlink-stop',
            'article': 'a',
            'verbose-name': 'tram stop',
            'verbose-name-plural': 'tram stops',
            'nearby': True, 'category': False,
            'uri-local': 'TramlinkStop',
        },
        'MET:DL': {
            'slug': 'dlr-station',
            'article': 'a',
            'verbose-name': 'DLR station',
            'verbose-name-plural': 'DLR stations',
            'nearby': True, 'category': False,
            'uri-local': 'DLRStation',
        },
        'MET:GL': {
            'slug': 'subway-station',
            'article': 'a',
            'verbose-name': 'Subway station',
            'verbose-name-plural': 'Subway stations',
            'nearby': True, 'category': False,
            'uri-local': 'SubwayStation',
        },
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
        'MET:NO': {
            'slug': 'net-stop',
            'article': 'a',
            'verbose-name': 'tram stop',
            'verbose-name-plural': 'tram stops',
            'nearby': True, 'category': False,
            'uri-local': 'NETStop',
        },
        'MET:SY': {
            'slug': 'supertram-stop',
            'article': 'a',
            'verbose-name': 'Supertram stop',
            'verbose-name-plural': 'Supertram stops',
            'nearby': True, 'category': False,
            'uri-local': 'SupertramStop',
        },
        'MET:TW': {
            'slug': 'tyne-and-wear-metro-station',
            'article': 'a',
            'verbose-name': 'Metro station',
            'verbose-name-plural': 'Metro stations',
            'nearby': True, 'category': False,
            'uri-local': 'TyneAndWearMetroStation',
        },
        'MET:WM': {
            'slug': 'midland-metro-stop',
            'article': 'a',
            'verbose-name': 'Midland Metro stop',
            'verbose-name-plural': 'Midland Metro stops',
            'nearby': True, 'category': False,
            'uri-local': 'MidlandMetroStation',
        },
        'GAT': {
            'slug': 'airport',
            'article': 'an',
            'verbose-name': 'airport',
            'verbose-name-plural': 'airports',
            'nearby': True, 'category': False,
            'uri-local': 'Airport',
        },
        'FER': {
            'slug': 'ferry-terminal',
            'article': 'a',
            'verbose-name': 'ferry terminal',
            'verbose-name-plural': 'ferry terminals',
            'nearby': True, 'category': False,
            'uri-local': 'FerryTerminal',
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
        self._method, self._areas = method, areas

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
        
        # Create a mapping from ATCO codes to CRS codes.
        f, filename =  tempfile.mkstemp()
        try:
            ftp.cwd("/V2/010/")
            ftp.retrbinary('RETR RailReferences.csv', data_chomper(f))
        except ftplib.error_temp:
            ftp = self._connect_to_ftp()
            ftp.cwd("/V2/010/")
            ftp.retrbinary('RETR RailReferences.csv', data_chomper(f))
        
        os.close(f)
        self._import_stations(open(filename, 'r'), self._source, self._entity_types[self.TRAIN_STATION])
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
        
        # Create a mapping from ATCO codes to CRS codes.
        f, filename =  tempfile.mkstemp()
        os.close(f)
        urllib.urlretrieve(self.HTTP_CSV_URL, filename)
        archive = zipfile.ZipFile(filename)
        if hasattr(archive, 'open'):
            f = archive.open('RailReferences.csv')
        else:
            f = StringIO(archive.read('RailReferences.csv'))
        
        self._import_stations(f, self._source, self._entity_types[self.TRAIN_STATION])
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

    def _import_stations(self, f, source, entity_type):
        
        # Delete any train stations from the main NaPTAN file
        for area in self._areas if self._areas != None else []:
            Entity.objects.filter(all_types_completion__slug='train-station',
                                  _identifiers__scheme='atco',
                                  _identifiers__value__startswith=str(area)).delete()
        
        csvfile = csv.reader(f)
        csvfile.next()

        for line in csvfile:
            atco, tiploc, crs, name, lang, grid_type, east, north, created, modified, rev, mod_type = line

            entity, created = Entity.objects.get_or_create(source=source, _identifiers__scheme='atco', _identifiers__value=atco)
            if modified == entity.metadata.get('naptan', {}).get('modified', ''):
                continue

            entity.title = name
            entity.location = entity.geometry = Point(int(east), int(north), srid=27700) # GB National Grid
            entity.primary_type = entity_type

            entity.metadata['naptan'] = {
                'modified': modified,
            }

            entity.save(identifiers={
                'atco': atco,
                'crs': crs,
                'tiploc': tiploc,
            })
            entity.all_types.add(entity_type)
            entity.update_all_types_completion()

    def _get_nptg(self, f):
        localities = {}
        csvfile = csv.reader(f)
        csvfile.next()
        for line in csvfile:
            localities[line[0]] = line[1]
        return localities

    def _get_entity_types(self):

        entity_types = {}
        for stop_type in self.entity_type_definitions:
            et = self.entity_type_definitions[stop_type]

            try:
                entity_type = EntityType.objects.get(slug=et['slug'])
            except EntityType.DoesNotExist:
                entity_type = EntityType(slug=et['slug'])

            entity_type.uri = "http://mollyproject.org/schema/maps#%s" % et['uri-local']
            entity_type.article = et['article']
            entity_type.verbose_name = et['verbose-name']
            entity_type.verbose_name_plural = et['verbose-name-plural']
            entity_type.show_in_nearby_list = et['nearby']
            entity_type.show_in_category_list = et['category']
            entity_type.save()

            entity_types[stop_type] = entity_type

        for stop_type, entity_type in entity_types.items():
            if entity_type.slug == 'public-transport-access-node':
                continue
            entity_type.subtype_of.add(entity_types[None])
            if str(stop_type).startswith('MET') and stop_type != 'MET':
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
