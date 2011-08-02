import base64
try:
    import cPickle as pickle
except ImportError:
    import pickle

from django.db import models

class CachedRoute(models.Model):
    
    hash = models.CharField(max_length=56, unique=True, primary_key=True)
    expires = models.DateTimeField()
    _cache = models.TextField()
    
    def _get_cache(self):
        return pickle.loads(base64.b64decode(self._cache))
    def _set_cache(self, value):
        self._cache = base64.b64encode(pickle.dumps(value))
    cache = property(_get_cache, _set_cache)
