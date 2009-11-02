import itertools, subprocess, os.path
from django.core.management.base import NoArgsCommand

from mobile_portal.osm.draw import get_map
from mobile_portal.oxpoints.models import Entity, EntityType

class Command(NoArgsCommand):

    ENTITY_TYPES = (
        'department', 'college', 'library', 'unit', 'museum',
        'pub', 'busstop', 'bicycle_parking'
    )
    ZOOM = 18
    
    QUALITY = 16384
    RESOLUTION = (QUALITY, int(QUALITY/1.2))
    
    TARGET_DIR = '/home/timf/'
    
    HIERACHY = ('college', 'department', 'unit', 'museum', 'library', 'pub', 'busstop')
    COLOURS = {
        'college': 'green',
        'department': 'blue',
        'unit': 'blue',
        'museum': 'amber',
        'library': 'red',
        'pub': 'yellow',
        'busstop': 'red',
    }
    
    def handle_noargs(self, **options):
        all_points = {}
        
        for entity_type_slug in Command.ENTITY_TYPES:
            entity_type = EntityType.objects.get(slug=entity_type_slug)
            entities = Entity.objects.filter(entity_type=entity_type)
            
            points = set()
            for entity in entities:
                if not entity.location:
                    continue

                points.add( (
                    entity.location[1],
                    entity.location[0],
                    'red',
                    None,
                ) )
                
                location = entity.location[1], entity.location[0]
                if not location in all_points:
                    all_points[location] = set()
                all_points[location].add(entity_type_slug)
                
            points = list(points)
            
            print "There are %d %s" % (len(points), entity_type.verbose_name_plural)
            continue
            get_map(
                points,
                Command.RESOLUTION[0],
                Command.RESOLUTION[1],
                os.path.join(Command.TARGET_DIR, entity_type_slug + '.png'),
                Command.ZOOM,
                51.7522, -1.2582
            )
            print "Generated for %s" % entity_type

        coloured_points = []            
        for point in all_points:
            for ptype in Command.HIERACHY:
                if ptype in all_points[point]:
                    break
            else:
                continue
                    
            coloured_points.append((
                point[0],
                point[1],
                Command.COLOURS[ptype],
                None,
            ))
            
        get_map(
            coloured_points,
            16384*3,
            int(16384*3/1.414),
            os.path.join(Command.TARGET_DIR, 'everything.png'),
            18,
            51.7522, -1.2582,
        )
        print 'Done BIG one'