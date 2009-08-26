try:
    import cPickle as pickle
except ImportError:
    import pickle
    
import hashlib, os.path
from datetime import datetime
from django.conf import settings
from models import GeneratedMap
from draw import get_map

MARKER_COLORS = (
    ('blue', '#0000ff', '#000050'),
    ('red', '#ff0000', '#500000'),
    ('yellow', '#f0ff00', '#4b5000'),
    ('green', '#00ff1e', '#005009'),
)

MARKER_RANGE = xrange(1, 100)


def get_generated_map(points, width, height):
    hash = hashlib.sha224(pickle.dumps(repr((points, width, height)))).hexdigest()[:16]
    
    try:
        gm = GeneratedMap.objects.get(hash=hash)
        gm.last_accessed = datetime.now()
        gm.save()
    except GeneratedMap.DoesNotExist:
        get_map(points, width, height, os.path.join(settings.GENERATED_MAP_DIR, hash))
        gm = GeneratedMap.objects.create(
            hash = hash,
            generated = datetime.utcnow(),
            last_accessed = datetime.utcnow(),
        )
    return hash