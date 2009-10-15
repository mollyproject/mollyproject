import itertools, subprocess, os.path
from django.core.management.base import NoArgsCommand

from mobile_portal.osm.draw import get_map
from mobile_portal.oxpoints.models import Entity, EntityType

class Command(NoArgsCommand):

    ENTITY_TYPES = (
        'library', #'department', #'college', 
        #'pub', #'busstop', 'bicycle_parking'
    )
    ZOOM = 15
    
    QUALITY = 2048
    RESOLUTION = (QUALITY, int(QUALITY/1.2))
    
    TARGET_DIR = '/home/alex/big_maps'
    
    
    def handle_noargs(self, **options):
        for entity_type_slug in Command.ENTITY_TYPES:
            entity_type = EntityType.objects.get(slug=entity_type_slug)
            entities = Entity.objects.filter(entity_type=entity_type, is_sublocation=False)
            
            points = []
            for entity in entities:
                if not entity.location:
                    continue

                points.append( (
                    entity.location[1],
                    entity.location[0],
                    'red',
                    None,
                ) )
            
            print "There are %d %s" % (len(points), entity_type.verbose_name_plural)
            get_map(
                points,
                Command.RESOLUTION[0],
                Command.RESOLUTION[1],
                os.path.join(Command.TARGET_DIR, entity_type_slug + '.png'),
                Command.ZOOM,
                51.7522, -1.2582
            )
            print "Generated for %s" % entity_type