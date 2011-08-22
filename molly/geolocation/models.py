from datetime import datetime, timedelta

import simplejson

from django.db import models

class RecentManager(models.Manager):
    def get_query_set(self):
        return super(RecentManager, self).get_query_set().filter(updated__gt=datetime.utcnow() - timedelta(14))

class Geocode(models.Model):
    lon = models.FloatField(null=True)
    lat = models.FloatField(null=True)
    query = models.TextField(null=True)

    _results = models.TextField(default='null')
    updated = models.DateTimeField()
    local_name = models.TextField()
    
    recent = RecentManager()
    objects = models.Manager()

    def _get_results(self):
        try:
            return self._cached_results
        except AttributeError:
            self._cached_results = simplejson.loads(self._results)
            return self._cached_results
    def _set_results(self, value):
        self._cached_results = value
    results = property(_get_results, _set_results)

    def save(self, *args, **kwargs):
        if hasattr(self, '_cached_results'):
            self._results = simplejson.dumps(self._cached_results)
        self.updated = datetime.utcnow()
        super(Geocode, self).save(*args, **kwargs)
