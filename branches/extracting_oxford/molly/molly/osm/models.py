try:
    import cPickle as pickle
except:
    import pickle
import hashlib, os, urllib, simplejson, sys
from datetime import datetime, timedelta
from StringIO import StringIO
from django.db import models, IntegrityError
from django.conf import settings

from molly.maps.models import Entity

class GeneratedMap(models.Model):
    hash = models.CharField(max_length=16, unique=True, primary_key=True)
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

    def delete(self, *args, **kwargs):
        try:
            os.unlink(self.get_filename())
        except:
            pass
        return super(GeneratedMap, self).delete(*args, **kwargs)

def get_tile_url(xtile, ytile, zoom):
    return "http://tile.openstreetmap.org/%d/%d/%d.png" % (zoom, xtile, ytile)

class OSMTile(models.Model):
    xtile = models.IntegerField()
    ytile = models.IntegerField()
    zoom = models.IntegerField()
    last_fetched = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (('xtile', 'ytile', 'zoom'),)

    def get_filename(self):
        if not os.path.exists(settings.OSM_TILE_DIR):
            os.mkdir(settings.OSM_TILE_DIR)
        return os.path.join(settings.OSM_TILE_DIR, "%d-%d-%d.png" % (self.xtile, self.ytile, self.zoom))

    @staticmethod
    def get_data(xtile, ytile, zoom):
        try:
            osm_tile = OSMTile.objects.get(xtile=xtile, ytile=ytile, zoom=zoom, last_fetched__gt = datetime.now() - timedelta(1))
            return open(osm_tile.get_filename())
        except (OSMTile.DoesNotExist, IOError):
            try:
                osm_tile, created = OSMTile.objects.get_or_create(xtile=xtile, ytile=ytile, zoom=zoom)
            except IntegrityError:
                return OSMTile.get_data(xtile, ytile, zoom)

            response = urllib.urlopen(get_tile_url(xtile, ytile, zoom))
            s = StringIO()
            s.write(response.read())
            f = open(osm_tile.get_filename(), 'w')
            f.write(s.getvalue())
            f.close()
            s.seek(0)
            return s
    
class OSMUpdate(models.Model):
    contributor_name = models.TextField(blank=True)
    contributor_email = models.TextField(blank=True)
    contributor_attribute = models.BooleanField()

    entity = models.ForeignKey(Entity)    
    
    submitted = models.DateTimeField(auto_now_add=True)
    
    old = models.TextField()
    new = models.TextField()
    
    notes = models.TextField(blank=True)
    
    approved = models.BooleanField(default=False)
    
