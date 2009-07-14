import random
from os.path import exists, join
import simplejson
from datetime import datetime, timedelta
from django.db import models
import django.dispatch

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

feed_fetched = django.dispatch.Signal(providing_args=['slug'])

class Feed(models.Model):
    slug = models.SlugField()
    url = models.URLField()
    fetch_period = models.PositiveIntegerField()
    last_fetched = models.DateTimeField()
    path = models.TextField(blank = True)
    
    def fetch(self):
        while not self.path or exists(self.get_path()):
            self.path = "%08x" % randint(0, 16**8-1)
        if self.last_fetched + timedelta(0, self.fetch_period) < datetime.now():
            require_save = True
            f = open(self.path, 'w')
            f.write(urllib.urlopen(self.url).read())
            f.close()
            self.last_fetched = datetime.now()
            self.save()
            
            feed_fetched.send(sender=self, slug=self.slug)
    
    def get_path(self):
        return join(settings.FEED_PATH, self.path)
           