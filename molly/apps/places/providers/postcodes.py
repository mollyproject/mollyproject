import simplejson
import urllib
import random
import csv
import zipfile
import tempfile
import urllib2
import os.path
import re

from datetime import timedelta
from django.db import transaction, reset_queries
from django.conf import settings
from django.contrib.gis.geos import Point
from django.utils.translation import ugettext_noop
from django.utils.translation import ugettext as _

from molly.apps.places.providers import BaseMapsProvider
from molly.apps.places.models import Entity, EntityType, Source, EntityTypeCategory
from molly.utils.i18n import override, set_name_in_language

from molly.conf.provider import task

class PostcodesMapsProvider(BaseMapsProvider):
    def __init__(self, codepoint_path, import_areas=None):
        self.codepoint_path = codepoint_path
        self.import_areas = import_areas

    CODEPOINT_OPEN_URL = 'http://freepostcodes.org.uk/static/code-point-open/codepo_gb.zip'
    MODULE_NAME = "molly.providers.apps.maps.postcodes"

    def _download_codepoint_open(self):

            archive_url = urllib2.urlopen(self.CODEPOINT_OPEN_URL)
            archive_file = open(self.codepoint_path, 'wb')
            archive_file.write(archive_url.read())
            archive_file.close()

    @task(run_every=timedelta(days=365))
    def import_data(self, **metadata):

        entity_type, source = self._get_entity_type(), self._get_source()
        
        if not os.path.exists(self.codepoint_path):
            self._download_codepoint_open()
        
        try:
            archive = zipfile.ZipFile(self.codepoint_path)
        except zipfile.BadZipfile:
            self._download_codepoint_open()
            archive = zipfile.ZipFile(self.codepoint_path)
        
        if self.import_areas:
            filenames = ['Code-Point Open/Data/%s.csv' % code.lower() for code in self.import_areas]
        else:
            filenames = [path for path in archive.namelist() if re.match(r'Code\-Point Open\/Data\/[a-z]{1,2}.csv', path)]

        for filename in filenames:
            reset_queries()
            with transaction.commit_on_success():
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
            postcode_abbrev = postcode_abbrev.replace(' ', '')
            
            # Now try to figure out where to put the space in
            if re.match(r'[A-Z][0-9]{2}[A-Z]{2}', postcode_abbrev):
                # A9 9AA
                postcode = '%s %s' % (postcode_abbrev[:2], postcode_abbrev[2:])
            elif re.match(r'[A-Z][0-9]{3}[A-Z]{2}', postcode_abbrev):
                # A99 9AA
                postcode = '%s %s' % (postcode_abbrev[:3], postcode_abbrev[3:])
            elif re.match(r'[A-Z]{2}[0-9]{2}[A-Z]{2}', postcode_abbrev):
                # AA9 9AA
                postcode = '%s %s' % (postcode_abbrev[:3], postcode_abbrev[3:])
            elif re.match(r'[A-Z]{2}[0-9]{3}[A-Z]{2}', postcode_abbrev):
                # AA99 9AA
                postcode = '%s %s' % (postcode_abbrev[:4], postcode_abbrev[4:])
            elif re.match(r'[A-Z][0-9][A-Z][0-9][A-Z]{2}', postcode_abbrev):
                # A9A 9AA
                postcode = '%s %s' % (postcode_abbrev[:3], postcode_abbrev[3:])
            elif re.match(r'[A-Z]{2}[0-9][A-Z][0-9][A-Z]{2}', postcode_abbrev):
                # AA9A 9AA
                postcode = '%s %s' % (postcode_abbrev[:4], postcode_abbrev[4:])
            else:
                postcode = postcode_abbrev
            
            try:
                easting, northing = int(easting), int(northing)
            except ValueError:
                continue
                
            j += 1
            
            try:
                entity = Entity.objects.get(source=source, _identifiers__scheme='postcode', _identifiers__value=postcode_abbrev)
            except Entity.DoesNotExist:
                entity = Entity(source=source)
            
            entity.location = Point(easting, northing, srid=27700)
            entity.geometry = entity.location
            entity.primary_type = entity_type
            
            identifiers = {
                'postcode': postcode_abbrev,
                'postcode-canonical': postcode,
            }
            entity.save(identifiers=identifiers)
            set_name_in_language(entity, 'en',
                                 title = postcode)
            entity.all_types.add(entity_type)
            entity.update_all_types_completion()

    def _get_entity_type(self):
        category, created = EntityTypeCategory.objects.get_or_create(name=ugettext_noop('Uncategorised'))
        verbose_names = {}
        for lang_code, lang_name in settings.LANGUAGES:
            verbose_names[lang_code] = (_('postcode'), _('a postcode'), _('postcodes'))
        defaults = {'verbose_names': verbose_names }
        entity_type, created = EntityType.objects.get_or_create(
            slug='post-code', category=category, defaults=defaults)
        if created:
            entity_type.show_in_nearby_list = False
            entity_type.show_in_category_list = False
            entity_type.save()
        return entity_type

    def _get_source(self):
        try:
            source = Source.objects.get(module_name=self.MODULE_NAME)
        except Source.DoesNotExist:
            source = Source(module_name=self.MODULE_NAME)

        source.name = "Postcodes"
        source.save()

        return source
