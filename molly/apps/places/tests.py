import unittest, random, urllib2, itertools

from django.core.management import call_command
from django.test.client import Client
from django.core.urlresolvers import reverse

from molly.apps.places.models import Entity, EntityType

class MapsTestCase(unittest.TestCase):
    def setUp(self):
        self.client = Client()
        
    def ensureBusstops(self):
        if Entity.objects.filter(entity_type__slug='busstop').count():
            return
        call_command('update_busstops')
    def ensureOxPoints(self):
        if Entity.objects.filter(entity_type__slug='college').count():
            return
        call_command('update_oxpoints')

    def testBusstops(self):
        return
        self.ensureBusstops()
        
        entities = random.sample(list(Entity.objects.filter(entity_type__source='naptan')), 20)
        client = Client()
        for entity in entities:
            try:
                r = client.get(entity.get_absolute_url())
            except urllib2.HTTPError, e:
                self.fail('Could not fetch %s: %s' % (entity.get_absolute_url(), unicode(e)))

    def testOxpoints(self):
        self.ensureOxPoints()

        entities = random.sample(list(Entity.objects.filter(entity_type__source='oxpoints')), 200)
        entities = Entity.objects.filter(entity_type__source='oxpoints')
        client = Client()
        for entity in entities:
            try:
                r = client.get(entity.get_absolute_url())
            except urllib2.HTTPError, e:
                self.fail('Could not fetch %s: %s' % (entity.get_absolute_url(), unicode(e)))
            except Exception, e:
                raise
    
    def testNearbyEntityWithoutLocation(self):
        self.ensureOxPoints()

        entities = list(Entity.objects.filter(location__isnull=True))
        entities = random.sample(entities, 5)
        
        entity_types = list(EntityType.objects.all())
        entity_types = random.sample(entity_types, 5)
        
        entities_with_types = zip(entities, entity_types)
        
        for entity, entity_type in entities_with_types:
            response = self.client.get(reverse(
                'maps_entity_nearby_detail', args=[
                    entity.entity_type.slug,
                    entity.display_id,
                    entity_type.slug,
                ]))
            self.assertEqual(response.template[0].name, 'maps/entity_without_location.xhtml')
                
    def testNearbyOxpoints(self):
        self.ensureOxPoints()

        def resolve_entity(p):
            if isinstance(p, int):
                return Entity.objects.get(oxpoints_id=p)
            elif isinstance(p, basestring):
                return Entity.objects.filter(title=p, entity_type__source='oxpoints')[0]
                
        NEARBY_ENTITIES = (
            ('Keble College', 'University Museum of Natural History'),
        )
        
        for p1, p2 in NEARBY_ENTITIES:
            p1, p2 = resolve_entity(p1), resolve_entity(p2)
            
            response = self.client.get(reverse(
                'maps_entity_nearby_detail', args=[
                    p1.entity_type.slug,
                    p1.display_id,
                    p2.entity_type.slug,
                ]))
            
            self.assertEqual(response.template[0].name, 'maps/nearby_detail.xhtml')
            self.assertTrue(p2 in itertools.chain(*response.context['entities']),
                "%s should be near %s." % (p1, p2)
            )
            self.assertTrue(response.context['entity'] == p1)