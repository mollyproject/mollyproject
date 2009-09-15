import unittest, random

from django.core.management import call_command
from django.test.client import Client
from django.core.urlresolvers import reverse

from mobile_portal.oxpoints.models import Entity, EntityType

class MapsTestCase(unittest.TestCase):
    def setUp(self):
        self.client = Client()
        
        if Entity.objects.count():
            return
            
        call_command('update_busstops')
        call_command('update_oxpoints')

    def testBusstops(self):
        entities = random.sample(list(Entity.objects.filter(entity_type__source='naptan')), 20)
        client = Client()
        for entity in entities:
            try:
                r = client.get(entity.get_absolute_url())
            except urllib2.HTTPError, e:
                self.fail('Could not fetch %s: %s' % (entity.get_absolute_url(), unicode(e)))

    def testOxpoints(self):
        entities = random.sample(list(Entity.objects.filter(entity_type__source='oxpoints')), 200)
        client = Client()
        for entity in entities:
            try:
                r = client.get(entity.get_absolute_url())
            except urllib2.HTTPError, e:
                self.fail('Could not fetch %s: %s' % (entity.get_absolute_url(), unicode(e)))
    
    def testNearbyEntityWithoutLocation(self):
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
        def resolve_entity(p):
            if isinstance(p, int):
                return Entity.objects.get(oxpoints_id=p)
            elif isinstance(p, basestring):
                return Entity.objects.filter(title=p, entity_type__source='oxpoints')[0]
                
        NEARBY_ENTITIES = (
            ('Keble College Lodge', 'University Museum of Natural History', 200),
        )
        
        for p1, p2, d in NEARBY_ENTITIES:
            p1, p2 = resolve_entity(p1), resolve_entity(p2)
            
            response = self.client.get(reverse(
                'maps_entity_nearby_detail_distance', args=[
                    p1.entity_type.slug,
                    p1.display_id,
                    p2.entity_type.slug,
                    d,
                ]))
            
            self.assertEqual(response.template[0].name, 'maps/nearby_detail.xhtml')
            self.assertTrue(p2 in response.context['entities'],
                "%s should be within %dm of %s." % (p1, d, p2)
            )
            self.assertTrue(response.context['entity'] == p1)