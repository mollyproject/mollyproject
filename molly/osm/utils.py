try:
    import cPickle as pickle
except ImportError:
    import pickle
    
import hashlib, os, os.path, logging, time
from datetime import datetime
from django.conf import settings
from django.db import IntegrityError
from models import GeneratedMap, get_generated_map_dir
from draw import get_map, get_fitted_map, MapGenerationError

MARKER_COLORS = (
    # name, fill, border, text
    ('amber', '#ff7e00', '#824000', '#000000'),
    ('blue', '#0000ff', '#000050', '#ffffff'),
    ('green', '#00ff1e', '#005009', '#000000'),
    ('purple', '#9146b8', '#3c1d4c', '#ffffff'),
    ('red', '#ff0000', '#500000', '#ffffff'),
    ('yellow', '#f0ff00', '#4b5000', '#000000'),
)

MARKER_RANGE = xrange(1, 100)

logger = logging.getLogger('molly.osm.generation')

def get_or_create_map(f, args):
    # This assumes that f is functional, i.e. its return value is determined
    # solely by its arguments. In the case that a map is requested again
    # before the original map generation has finished, the following happens:
    # * Nothing has yet been saved to the database as we have to wait for the
    #   metadata to come back. Hence, we get a DoesNotExist.
    # * The map is regenerated. Due to the atomic nature of filesystem writes
    #   we can guarantee that we won't get a funnily spliced file written by
    #   the function f.
    # * The first call saves the GeneratedMap instance to the database.
    # * The second call attempts to do the same, but it would result in a
    #   duplicate primary key, and so it throws an IntegrityError.
    # * Due to the functional nature of f, we know we have the correct metadata
    #   for the map that has been generated, and that it will match that
    #   already stored in the database. As such, we can leave the database
    #   alone and return the metadata just generated.
    # Assuming that if we get a DoesNotExist that there won't be one by the
    # time we come to write leads to a race condition given the non-zero
    # duration of f. Subsequent attempts to get the map with that hash then
    # throws a MultipleObjectsReturned exception. Yes, this did happen. Seven
    # times, no less.

    start_time = time.time()
    
    hash = hashlib.sha224(pickle.dumps(repr(args))).hexdigest()[:16]
    
    try:
        gm = GeneratedMap.objects.get(hash=hash)
        gm.last_accessed = datetime.utcnow()
        gm.save()
        metadata = gm.metadata
        if gm.faulty:
            gm.delete()
            logger.debug("Found previously generated map: %s, but it's faulty, so regenerating", hash)
            raise GeneratedMap.DoesNotExist()
        else:
            logger.debug("Found previously generated map: %s", hash)
    except GeneratedMap.DoesNotExist:
        generated_map_dir = get_generated_map_dir()
        if not os.path.exists(generated_map_dir):
            os.makedirs(generated_map_dir)
        try:
            metadata = f(filename=os.path.join(generated_map_dir, hash), *args)
            faulty = False
        except MapGenerationError as e:
            # If a map generation error occurs, then mark this map as faulty
            # this means that it is deleted next time it is requested, forcing
            # it to be re-generated next time (hopefully the error is transient)
            logger.warning("Unable to generate map")
            metadata = e.metadata
            faulty = True
        
        gm = GeneratedMap(
            hash = hash,
            generated = datetime.utcnow(),
            last_accessed = datetime.utcnow(),
            faulty = faulty,
        )
        gm.metadata = metadata
        try:
            gm.save()
        except IntegrityError:
            logger.debug("Map generated: %s, took %.5f seconds (with race)", (hash, time.time()-start_time)) 
        else:
            logger.debug("Map generated: %s, took %.5f seconds", (hash, time.time()-start_time)) 
    
        if GeneratedMap.objects.all().count() > 25000:
            youngest = None
            for gm in GeneratedMap.objects.order_by('last_accessed')[:50]:
                if not youngest:
                    youngest = gm.last_accessed
                gm.delete()
            age = (datetime.now()-youngest)
            age = age.days*24 + age.seconds/3600.0
            logger.debug("Cleared out old maps, youngest is %f hours", age)
                
        
    return hash, metadata


def get_generated_map(points, width, height):
    return get_or_create_map(get_map, (points, width, height))
    
def fit_to_map(centre_point, points, min_points, zoom, width, height):
    points = list(points)
    return get_or_create_map(get_fitted_map, (centre_point, points, min_points, zoom, width, height))
