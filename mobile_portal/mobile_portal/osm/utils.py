try:
    import cPickle as pickle
except ImportError:
    import pickle
    
import hashlib, os, os.path
from datetime import datetime
from django.conf import settings
from models import GeneratedMap
from draw import get_map, get_fitted_map

MARKER_COLORS = (
    ('blue', '#0000ff', '#000050', '#ffffff'),
    ('red', '#ff0000', '#500000', '#ffffff'),
    ('yellow', '#f0ff00', '#4b5000', '#000000'),
    ('green', '#00ff1e', '#005009', '#000000'),
    ('purple', '#9146b8', '#3c1d4c', '#ffffff'),
    ('amber', '#ff7e00', '#824000', '#000000'),
)

MARKER_RANGE = xrange(1, 100)

def get_or_create_map(f, args):
    hash = hashlib.sha224(pickle.dumps(repr(args))).hexdigest()[:16]
    
    try:
        gm = GeneratedMap.objects.get(hash=hash)
        gm.last_accessed = datetime.utcnow()
        gm.save()
        metadata = gm.metadata
    except GeneratedMap.DoesNotExist:
        if not os.path.exists(settings.GENERATED_MAP_DIR):
            os.makedirs(settings.GENERATED_MAP_DIR)
        metadata = f(filename=os.path.join(settings.GENERATED_MAP_DIR, hash), *args)
        gm = GeneratedMap(
            hash = hash,
            generated = datetime.utcnow(),
            last_accessed = datetime.utcnow(),
        )
        gm.metadata = metadata
        gm.save()
    return hash, metadata


def get_generated_map(points, width, height):
    return get_or_create_map(get_map, (points, width, height))
    
def fit_to_map(centre_point, points, min_points, zoom, width, height):
    points = list(points)
    return get_or_create_map(get_fitted_map, (centre_point, points, min_points, zoom, width, height))
