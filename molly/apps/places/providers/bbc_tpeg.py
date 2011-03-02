import os, os.path, urllib, random, zipfile, tempfile
from lxml import etree

from django.contrib.gis.geos import Point, LineString
from django.conf import settings

from molly.apps.places.providers import BaseMapsProvider
from molly.apps.places.models import Source, Entity, EntityType, EntityTypeCategory
from molly.conf.settings import batch

class BBCTPEGResolver(etree.Resolver):
    """
    Resolves the DTD references in a BBC TPEG feed.
    
    Fetches and unzips the DTDs and entity references, storing them locally
    in $CACHE_DIR/bbc_tpeg/.
    """
    
    _DTD_URLS = (
        'http://www.bbc.co.uk/travelnews/xml/tpegml_dtds.zip',
        'http://www.bbc.co.uk/travelnews/xml/english_ent.zip',
    )
    
    _RESOLVE_DIR = os.path.join(settings.CACHE_DIR, 'bbc_tpeg')

    def resolve(self, url, context, id):
        if not os.path.exists(self._RESOLVE_DIR):
            self._fetch_dtds()
        filename = os.path.join(self._RESOLVE_DIR, url.split('/')[-1])
        return self.resolve_filename(filename, context)
    
    def _fetch_dtds(self):
        os.makedirs(self._RESOLVE_DIR)
        for url in self._DTD_URLS:
            f, filename = tempfile.mkstemp()
            try:
                os.close(f)
                urllib.urlretrieve(url, filename)
                archive = zipfile.ZipFile(filename)
                archive.extractall(self._RESOLVE_DIR)
            finally:
                os.unlink(filename)

class BBCTPEGPlacesProvider(BaseMapsProvider):
    _TPEG_URL = 'http://www.bbc.co.uk/travelnews/tpeg/en/local/rtm/rtm_tpeg.xml'
    
    def __init__(self, url=_TPEG_URL):
        self._tpeg_url = url
    
    @batch('%d-59/3 * * * *' % random.randint(0, 2))
    def import_data(self, metadata, output):
        source, entity_type = self._get_source(), self._get_entity_type()
        
        parser = etree.XMLParser(load_dtd=True)
        parser.resolvers.add(BBCTPEGResolver())
        xml = etree.parse(urllib.urlopen(self._tpeg_url), parser=parser)
        
        entities, seen = {}, set()
        for entity in Entity.objects.filter(source=source):
            if 'bbc-tpeg' in entity.identifiers:
                entities[entity.identifiers['bbc-tpeg']] = entity
        
        for message in xml.getroot().findall('tpeg_message'):
            id = message.find('road_traffic_message').attrib['message_id']
            road_traffic_message = message.find('road_traffic_message')
            
            try:
                entity = entities[id]
            except KeyError:
                entity = Entity()
                entities[id] = entity
            
            entity.source = source
            entity.title = message.find('summary').text
            entity.primary_type = entity_type
            
            locs = map(self._wgs84_to_point, road_traffic_message.findall('location_container/location_coordinates/WGS84'))
            if len(locs) > 1:
                entity.geometry = LineString(*locs)
            elif len(locs) == 1:
                entity.geometry = locs[0]
            else:
                continue
            entity.location = Point(
                sum(p.x for p in locs)/len(locs), 
                sum(p.y for p in locs)/len(locs), 
                srid=4326,
            )
            
            entity.metadata['bbc_tpeg'] = {
                'xml': etree.tostring(message),
                'severity': road_traffic_message.attrib['severity_factor'],
                'generated': road_traffic_message.attrib['message_generation_time'],
                'version': int(road_traffic_message.attrib['version_number']),
            }
            
            entity.save(identifiers={'bbc-tpeg': id})
            entity.all_types = [entity_type]
            entity.update_all_types_completion()
            seen.add(entity.pk)
        
        for entity in Entity.objects.filter(source=source):
            if not entity.pk in seen:
                entity.delete()
    
    def _wgs84_to_point(self, elem):
        attrib = elem.attrib
        return Point(float(attrib['longitude']), float(attrib['latitude']), srid=4326)

    def _get_source(self):
        try:
            source = Source.objects.get(module_name="molly.providers.apps.maps.bbc_tpeg")
        except Source.DoesNotExist:
            source = Source(module_name="molly.providers.apps.maps.bbc_tpeg")

        source.name = "BBC TPEG"
        source.save()

        return source
    
    def _get_entity_type(self):
        entity_type, created = EntityType.objects.get_or_create(slug='travel-alert')
        category, _ = EntityTypeCategory.objects.get_or_create(name='Transport')
        entity_type.verbose_name = 'travel alert'
        entity_type.verbose_name_plural = 'travel alerts'
        entity_type.article = 'a'
        if created:
            entity_type.show_in_nearby_list = False
            entity_type.show_in_category_list = False
        entity_type.category = category
        entity_type.save()
        return entity_type
