import simplejson
from datetime import datetime, timedelta
from django.db import models

class RecentManager(models.Manager):
    def get_query_set(self):
        return super(RecentManager, self).get_query_set().filter(last_updated__gt = datetime.now() - timedelta(14))

class Placemarks(models.Model):
    _data = models.TextField(default='null')
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)
    query = models.TextField(blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    recent = RecentManager()
    objects = models.Manager()

    def get_data(self):
        if not hasattr(self, 'data_json'):
            self.data_json = simplejson.loads(self._data)
        return self.data_json
    def set_data(self, data):
        self.data_json = data
    data = property(get_data, set_data)
    
    def save(self, force_insert=False, force_update=False):
        print self.data
        self._data = simplejson.dumps(self.data)
        super(Placemarks, self).save()       