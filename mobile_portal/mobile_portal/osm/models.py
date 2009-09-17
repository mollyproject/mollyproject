try:
    import cPickle as pickle
except:
    import pickle
import hashlib, os, urllib, simplejson
from datetime import datetime, timedelta
from django.db import models
from django.conf import settings

class GeneratedMap(models.Model):
    hash = models.CharField(max_length=16)
    generated = models.DateTimeField()
    last_accessed = models.DateTimeField()
    _metadata = models.TextField(blank=True)
    
    def _get_metadata(self):
        return simplejson.loads(self._metadata)
    def _set_metadata(self, value):
        self._metadata = simplejson.dumps(value)
    metadata = property(_get_metadata, _set_metadata)
    
    def get_filename(self):
        if not os.path.exists(settings.GENERATED_MAP_DIR):
            os.mkdir(settings.GENERATED_MAP_DIR)
        return os.path.join(settings.GENERATED_MAP_DIR, self.hash)

def get_tile_url(xtile, ytile, zoom):
    return "http://tile.openstreetmap.org/%d/%d/%d.png" % (zoom, xtile, ytile)

class OSMTile(models.Model):
    xtile = models.IntegerField()
    ytile = models.IntegerField()
    zoom = models.IntegerField()
    last_fetched = models.DateTimeField(auto_now=True)
    
    def get_filename(self):
        if not os.path.exists(settings.OSM_TILE_DIR):
            os.mkdir(settings.OSM_TILE_DIR)
        return os.path.join(settings.OSM_TILE_DIR, "%d-%d-%d.png" % (self.xtile, self.ytile, self.zoom))
    
    @staticmethod
    def get_data(xtile, ytile, zoom):
        try:
            osm_tile = OSMTile.objects.get(xtile=xtile, ytile=ytile, zoom=zoom, last_fetched__lt = datetime.now() - timedelta(1))
        except OSMTile.DoesNotExist:
            osm_tile, created = OSMTile.objects.get_or_create(xtile=xtile, ytile=ytile, zoom=zoom)
            
            response = urllib.urlopen(get_tile_url(xtile, ytile, zoom))
            f = open(osm_tile.get_filename(), 'w')
            f.write(response.read())
            f.close()
            
        return open(osm_tile.get_filename())