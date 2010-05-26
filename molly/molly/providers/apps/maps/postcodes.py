import simplejson, urllib, random, csv, zipfile
from StringIO import StringIO

from django.contrib.gis.geos import Point

from molly.apps.places.providers import BaseMapsProvider
from molly.apps.places.models import Entity, EntityType, Source

from molly.conf.settings import batch


OXPOINTS_NS = 'http://ns.ox.ac.uk/namespace/oxpoints/2009/02/owl#'

class PostcodesMapsProvider(BaseMapsProvider):
    def __init__(self, codepoint_path, import_areas=None):
        self.codepoint_path = codepoint_path
        self.import_areas = import_areas

    @batch('%d 12 1 1 *' % random.randint(0, 59))
    def import_data(self, metadata, output):

        entity_type, source = self._get_entity_type(), self._get_source()

        archive = zipfile.ZipFile(self.codepoint_path)
        if self.import_areas:
            filenames = ['Code-Point Open/data/CSV/%s.csv' % code.lower() for code in self.import_areas]
        else:
            filenames = [path for path in archive.listnames() if re.match(r'Code\-Point Open\/data\/CSV\/[a-z]{1,2}.csv', path)]

        for filename in filenames:
            if hasattr(archive, 'open'):
                f = archive.open(filename)
            else:
                f = StringIO(filename)
            reader = csv.reader(f)
            
            self._load_from_csv(reader, entity_type, source)

    def _load_from_csv(self, reader, entity_type, source):
        j = 0
        for i, line in enumerate(reader):
            postcode_abbrev, (easting, northing) = line[0], line[10:12]
            if postcode_abbrev[3] != ' ':
                postcode = '%s %s' % (postcode_abbrev[:3], postcode_abbrev[3:])
            else:
                postcode = postcode_abbrev
            
            if not (i % 100):
                print "%7d %7d %s" % (i, j, postcode)
                
            try:
                easting, northing = int(easting), int(northing)
            except ValueError:
                continue
                
            j += 1
            
            try:
                entity = Entity.objects.get(source=source, _identifiers__scheme='postcode-abbrev', _identifiers__value=postcode_abbrev)
            except Entity.DoesNotExist:
                entity = Entity(source=source)
            
            entity.title = postcode
            entity.location = Point(easting, northing, srid=27700)
            entity.geometry = entity.location
            entity.primary_type = entity_type
            
            identifiers = {
                'postcode': postcode_abbrev,
            }
            entity.save(identifiers=identifiers)
            entity.all_types.add(entity_type)

    def _get_entity_type(self):
        try:
            return EntityType.objects.get(slug='post-code')
        except EntityType.DoesNotExist:
            entity_type = EntityType(
                slug = 'post-code',
                article = 'a',
                verbose_name = 'postcode',
                verbose_name_plural = 'postcodes',
                show_in_nearby_list = False,
                show_in_category_list = False,
            )
            entity_type.save()
            return entity_type

    def _get_source(self):
        try:
            source = Source.objects.get(module_name="molly.providers.apps.maps.postcodes")
        except Source.DoesNotExist:
            source = Source(module_name="molly.providers.apps.maps.postcodes")

        source.name = "Postcodes"
        source.save()

        return source