import simplejson
import urllib
import random
import csv
import zipfile
import tempfile
import urllib2
import os.path
import re

from django.contrib.gis.geos import Point

from molly.apps.places.providers import BaseMapsProvider
from molly.apps.places.models import Entity, EntityType, Source, EntityTypeCategory

from molly.conf.settings import batch

class PostcodesMapsProvider(BaseMapsProvider):
    def __init__(self, codepoint_path, import_areas=None):
        self.codepoint_path = codepoint_path
        self.import_areas = import_areas

    @batch('%d 12 1 1 *' % random.randint(0, 59))
    def import_data(self, metadata, output):

        entity_type, source = self._get_entity_type(), self._get_source()

        if not os.path.exists(self.codepoint_path):
            archive_url = urllib2.urlopen('http://freepostcodes.org.uk/static/code-point-open/codepo_gb.zip')
            archive_file = open(self.codepoint_path, 'w')
            archive_file.write(archive_url.read())
            archive_file.close()
        
        archive = zipfile.ZipFile(self.codepoint_path)
        
        if self.import_areas:
            filenames = ['Code-Point Open/Data/%s.csv' % code.lower() for code in self.import_areas]
        else:
            filenames = [path for path in archive.namelist() if re.match(r'Code\-Point Open\/Data\/[a-z]{1,2}.csv', path)]

        for filename in filenames:
            if hasattr(archive, 'open'):
                f = archive.open(filename)
            else:
                f = tempfile.TemporaryFile()
                f.write(archive.read(filename))
                f.seek(0)
            reader = csv.reader(f)
            self._load_from_csv(reader, entity_type, source)
            del f

    def _load_from_csv(self, reader, entity_type, source):
        j = 0
        for i, line in enumerate(reader):
            postcode_abbrev, (easting, northing) = line[0], line[10:12]
            if postcode_abbrev[-4] != ' ':
                postcode = '%s %s' % (postcode_abbrev[:-3], postcode_abbrev[-3:])
            else:
                postcode = postcode_abbrev
            postcode_abbrev = postcode_abbrev.replace(' ', '')
                
            try:
                easting, northing = int(easting), int(northing)
            except ValueError:
                continue
                
            j += 1
            
            try:
                entity = Entity.objects.get(source=source, _identifiers__scheme='postcode', _identifiers__value=postcode_abbrev)
            except Entity.DoesNotExist:
                entity = Entity(source=source)
            
            entity.title = postcode
            entity.location = Point(easting, northing, srid=27700)
            entity.geometry = entity.location
            entity.primary_type = entity_type
            
            identifiers = {
                'postcode': postcode_abbrev,
                'postcode-canonical': postcode,
            }
            entity.save(identifiers=identifiers)
            entity.all_types.add(entity_type)
            entity.update_all_types_completion()

    def _get_entity_type(self):
        category, _ = EntityTypeCategory.objects.get_or_create(name='Uncategorised')
        entity_type, created = EntityType.objects.get_or_create(
            slug='post-code', category=category)
        entity_type.slug = 'post-code'
        entity_type.article = 'a'
        entity_type.verbose_name = 'postcode'
        entity_type.verbose_name_plural = 'postcodes'
        if created:
            entity_type.show_in_nearby_list = False
            entity_type.show_in_category_list = False
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
