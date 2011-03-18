import unittest, random, urllib2, itertools

from django.core.management import call_command
from django.test.client import Client
from django.core.urlresolvers import reverse

from molly.apps.places.models import Entity, EntityType
from molly.apps.places.providers import NaptanMapsProvider
from secrets import SECRETS

class MapsTestCase(unittest.TestCase):
    def setUp(self):
        self.client = Client()
        
    def ensureBusstops(self):
        if Entity.objects.filter(all_types__slug='busstop').count():
            return
        NaptanMapsProvider(method='http').import_data(None, None)

    def testBusstops(self):
        self.ensureBusstops()
        
        entities = random.sample(list(Entity.objects.filter(entity_type__source='naptan')), 20)
        client = Client()
        for entity in entities:
            try:
                r = client.get(entity.get_absolute_url())
            except urllib2.HTTPError, e:
                self.fail('Could not fetch %s: %s' % (entity.get_absolute_url(), unicode(e)))
    
    def testNearbyEntityWithoutLocation(self):
        self.ensureBusstops()

        entities = list(Entity.objects.filter(location__isnull=True))
        entities = random.sample(entities, 5)
        
        entity_types = list(EntityType.objects.all())
        entity_types = random.sample(entity_types, 5)
        
        entities_with_types = zip(entities, entity_types)
        
        for entity, entity_type in entities_with_types:
            response = self.client.get(reverse(
                'entity-nearby-detail', args=[
                    entity.all_types.all()[0].slug,
                    entity.display_id,
                    entity_type.slug,
                ]))
            self.assertEqual(response.template[0].name, 'maps/entity_without_location.xhtml')