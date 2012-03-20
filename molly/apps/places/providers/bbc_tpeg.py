import os, os.path, urllib, random, zipfile, tempfile
from lxml import etree
from datetime import timedelta

from django.contrib.gis.geos import Point, LineString
from django.conf import settings
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_noop

from molly.apps.places.providers import BaseMapsProvider
from molly.apps.places.models import Source, Entity, EntityType, EntityTypeCategory
from molly.conf.provider import task
from molly.utils.i18n import override, set_name_in_language

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
    
    @task(run_every=timedelta(minutes=3))
    def import_data(self, **metadata):
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
            set_name_in_language(entity, 'en',
                                 title = message.find('summary').text)
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
        try:
            entity_type = EntityType.objects.get(slug='travel-alert')
            created = False
        except EntityType.DoesNotExist:
            entity_type = EntityType(slug='travel-alert')
            created = True
        category, etc_created = EntityTypeCategory.objects.get_or_create(name=ugettext_noop('Transport'))
        if created:
            entity_type.show_in_nearby_list = False
            entity_type.show_in_category_list = False
        entity_type.category = category
        entity_type.save()
        for lang_code, lang_name in settings.LANGUAGES:
            with override(lang_code):
                set_name_in_language(entity_type, lang_code,
                                     verbose_name=_('travel alert'),
                                     verbose_name_singular=_('a travel alert'),
                                     verbose_name_plural=_('travel alerts'))
        return entity_type
