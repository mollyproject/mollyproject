import rdflib, Queue, csv
from django.core.management.base import NoArgsCommand
from django.db import transaction
from django.contrib.gis.geos import Point
from mobile_portal.oxpoints.models import Entity, EntityType


OXPOINTS_NS = 'http://ns.ox.ac.uk/namespace/oxpoints/2009/02/owl#'

class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list
    help = "Loads OxPoints data from http://m.ox.ac.uk/oxpoints/all.xml"

    requires_model_validation = True

    def load_entity_type(self):
        """
        Load the post code entity type into the database, returning the created
        """

        entity_type, created = EntityType.objects.get_or_create(slug='postcode')
        entity_type.article = 'a'
        entity_type.verbose_name = 'post code'
        entity_type.verbose_name_plural = 'post codes'
        entity_type.id_field = 'post_code'
        entity_type.source = 'postcode'
        entity_type.show_in_nearby_list = False
        entity_type.show_in_category_list = False
        entity_type.save()
        
        return entity_type

    def handle_noargs(self, **options):
        
        entity_type = self.load_entity_type()
        valid_areas = ('OX', 'GL', 'CV', 'NN', 'MK', 'HP', 'SL', 'RG', 'SN')
        
        reader = csv.reader(open('/home/alex/NSPDF_AUG_2009_UK_1M_FP.csv', 'r'))
        
        j = 0
        for i, line in enumerate(reader):
            post_code, (easting, northing) = line[2], line[9:11]
            
            if not (i % 100):
                print "%7d %7d %s" % (i, j, post_code)
                
            try:
                easting, northing = int(easting), int(northing)
            except ValueError:
                continue
                
            if post_code[:2] not in valid_areas:
                continue
                
            j += 1
            
            try:
                entity = Entity.objects.get(entity_type=entity_type, post_code=post_code.replace(' ',''))
            except Entity.DoesNotExist:
                entity = Entity(entity_type=entity_type, post_code=post_code.replace(' ',''))
            
            entity.title = post_code
            entity.location = Point(easting, northing, srid=27700)
            entity.geometry = entity.location
            
            entity.save()
            entity.all_types.add(entity_type)
            
