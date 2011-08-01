try:
    import cPickle as pickle
except ImportError:
    import pickle
import hashlib
import os
import os.path
import logging
import time
from datetime import datetime, timedelta

from django.db import IntegrityError, transaction

from molly.maps.osm.models import GeneratedMap, get_generated_map_dir
from molly.maps.osm.draw import get_fitted_map, MapGenerationError

MARKER_COLORS = (
    # name, fill, border, text
    ('amber', '#ff7e00', '#824000', '#000000'),
    ('blue', '#0000ff', '#000050', '#ffffff'),
    ('green', '#00ff1e', '#005009', '#000000'),
    ('purple', '#9146b8', '#3c1d4c', '#ffffff'),
    ('red', '#ff0000', '#500000', '#ffffff'),
    ('yellow', '#f0ff00', '#4b5000', '#000000'),
)

MARKER_RANGE = xrange(1, 200)

logger = logging.getLogger(__name__)

def get_or_create_map(generator, args):
    """
    A wrapper function for a map generator which protects against race
    conditions in map generation. You should use this instead of calling a
    generator directly.
    
    @param generator: The generator to use
    @param args: Any extra arguments to pass to the generator function
    
    This assumes that generator is functional, i.e. its return value is
    determined solely by its arguments. In the case that a map is requested
    again before the original map generation has finished, the following
    happens:
    * Nothing has yet been saved to the database as we have to wait for the
      metadata to come back. Hence, we get a DoesNotExist.
    * The map is regenerated. Due to the atomic nature of filesystem writes
      we can guarantee that we won't get a funnily spliced file written by
      the function f.
    * The first call saves the GeneratedMap instance to the database.
    * The second call attempts to do the same, but it would result in a
      duplicate primary key, and so it throws an IntegrityError.
    * Due to the functional nature of f, we know we have the correct metadata
      for the map that has been generated, and that it will match that
      already stored in the database. As such, we can leave the database
      alone and return the metadata just generated.
    Assuming that if we get a DoesNotExist that there won't be one by the
    time we come to write leads to a race condition given the non-zero
    duration of f. Subsequent attempts to get the map with that hash then
    throws a MultipleObjectsReturned exception. Yes, this did happen. Seven
    times, no less.
    """

    start_time = time.time()
    
    # Generate a hash based on the arguments for this map
    hash = hashlib.sha224(pickle.dumps(repr(args))).hexdigest()[:16]
    
    # Try fetching the map if it already exists
    try:
        generated_map = GeneratedMap.objects.get(hash=hash)
        generated_map.last_accessed = datetime.utcnow()
        generated_map.save()
        metadata = generated_map.metadata
        
        # Except if the current map is marked as faulty (e.g., missing OSM tile,
        # in which case we delete it and raise DoesNotExist to get it
        # regenerated)
        if generated_map.faulty:
            generated_map.delete()
            logger.debug("Found previously generated map: %s, but it's " + \
                         "faulty, so regenerating", hash)
            raise GeneratedMap.DoesNotExist()
        else:
            logger.debug("Found previously generated map: %s", hash)
            
    
    # If it doesn't exist, generate it
    except GeneratedMap.DoesNotExist:
        generated_map_dir = get_generated_map_dir()
        if not os.path.exists(generated_map_dir):
            os.makedirs(generated_map_dir)
        try:
            # Call the generator to generate it
            metadata = generator(filename=os.path.join(generated_map_dir, hash),
                                 *args)
        except MapGenerationError as e:
            # If a map generation error occurs, then mark this map as faulty
            # this means that it is deleted next time it is requested, forcing
            # it to be re-generated next time (hopefully the error is transient)
            metadata = e.metadata
            faulty = True
        else:
            # If no exception was raised, we mark it as non-faulty
            faulty = False
        
        generated_map = GeneratedMap(
            hash = hash,
            generated = datetime.utcnow(),
            last_accessed = datetime.utcnow(),
            faulty = faulty,
        )
        generated_map.metadata = metadata
        
        # This may fail, so we use a transaction savepoint in case we need to
        # roll back the transaction - not doing this causes any future database
        # queries to fail
        savepoint = transaction.savepoint()
        try:
            generated_map.save()
        except IntegrityError:
            # This means a race error was generated, but because of the
            # functional nature of generator, we can carry on here
            logger.debug("Map generated: %s, took %.5f seconds (with race)",
                         hash, time.time()-start_time)
            transaction.savepoint_rollback(savepoint)
        else:
            logger.debug("Map generated: %s, took %.5f seconds",
                         hash, time.time()-start_time)
            transaction.savepoint_commit(savepoint)
        
        # If there are any maps older than a week, regenerate them
        to_delete = GeneratedMap.objects.filter(
          generated__lt=datetime.now()-timedelta(weeks=1)).order_by('generated')
        if to_delete.count() > 0:
            # But only clear up 50 at a time
            try:
                youngest = to_delete[0].last_accessed
                to_delete = to_delete[:50]
                for generated_map in to_delete:
                    generated_map.delete()
                age = (datetime.now()-youngest)
                age = age.days*24 + age.seconds/3600.0
                logger.info("Cleared out old maps, youngest is %f hours", age)
            except IndexError:
                logger.info("Maps disappeared whilst trying to delete - race condition?", exc_info=True)
    
    return hash, metadata
    
def fit_to_map(centre_point, points, min_points, zoom, width, height,
               extra_points, paths):
    """
    Given a list of points and some minimum number of points, then a "fitted
    map" is generated, which is one which contains at least @C{min_points}, and
    is at least at the zoom level @C{zoom}, but also contains any other points
    in the list which is inside the bounding area of this minimal map. This
    uses the @C{get_or_create_map} wrapper to protect against race conditions.
    
    Valid colours in point definitions below are defined in @C{MARKER_COLOURS}
    
    @param centre_point: A tuple of longitude, latitude and colour corresponding
                         to the "centre" of the map. This is NOT the central
                         latitude/longitude of the generated image, which is
                         simply the middle of the set of points passed in, but
                         simply a special marker which is indicated with a star.
    @type centre_point: (float, float, str) or None
    @param points: An (ordered) list of points to be plotted on the map. These
                   are indicated on the map with numbered markers. This list
                   consists of tuples of longitude, latitude and a string
                   indicating the colours of the markers to be rendered.
    @type points: [(float, float, str)]
    @param min_points: The minimum number of points to be displayed on the
                       resulting map
    @type min_points: int
    @param zoom: A bound on the maximum zoom level to be rendered. If this zoom
                 level is too small to fit @C{min_points} points on it, then the
                 map will be zoomed out further to fit in. If this is None, then
                 this is equivalent to the smallest zoom level.
    @type zoom: int
    @param width: The width of the generated map image, in pixels
    @type width: int
    @param height: The height of the generated map image, in pixels
    @type height: int
    """
    points = list(points)
    return get_or_create_map(get_fitted_map,
                             (centre_point, points, min_points,
                              zoom, width, height, extra_points, paths))
