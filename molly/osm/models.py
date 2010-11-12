try:
    import cPickle as pickle
except:
    import pickle
import hashlib, os, urllib, simplejson, sys
from datetime import datetime, timedelta
from StringIO import StringIO
from django.db import models, IntegrityError
from django.conf import settings

from molly.apps.places.models import Entity

def get_generated_map_dir():
    return getattr(settings, 'GENERATED_MAP_DIR', os.path.join(settings.CACHE_DIR, 'generated_maps'))

def get_marker_dir():
    return getattr(settings, 'MARKER_DIR', os.path.join(settings.CACHE_DIR, 'markers'))

def get_osm_tile_dir():
    return getattr(settings, 'OSM_TILE_DIR', os.path.join(settings.CACHE_DIR, 'osm_tiles'))

class GeneratedMap(models.Model):
    hash = models.CharField(max_length=16, unique=True, primary_key=True)
    generated = models.DateTimeField()
    last_accessed = models.DateTimeField()
    _metadata = models.TextField(blank=True)
    faulty = models.BooleanField(default=False)

    def _get_metadata(self):
        return simplejson.loads(self._metadata)
    def _set_metadata(self, value):
        self._metadata = simplejson.dumps(value)
    metadata = property(_get_metadata, _set_metadata)

    def get_filename(self):
        generated_map_dir = get_generated_map_dir()
        if not os.path.exists(generated_map_dir):
            os.mkdir(generated_map_dir)
        return os.path.join(generated_map_dir, self.hash)

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
        osm_tile_dir = get_osm_tile_dir()
        if not os.path.exists(osm_tile_dir):
            os.mkdir(osm_tile_dir)
        return os.path.join(osm_tile_dir, "%d-%d-%d.png" % (self.xtile, self.ytile, self.zoom))

    @staticmethod
    def get_data(xtile, ytile, zoom, retry=True):
        """
        Fetch an OSM tile from the OSM tile server, and cache it if necessary.
        If the last argument is True, then a retry to get data from the tile
        server is attempted if the first attempt fails.
        """
        try:
            osm_tile = OSMTile.objects.get(xtile=xtile, ytile=ytile, zoom=zoom, last_fetched__gt = datetime.now() - timedelta(1))
            return open(osm_tile.get_filename())
        except (OSMTile.DoesNotExist, IOError):
            try:
                osm_tile, created = OSMTile.objects.get_or_create(xtile=xtile, ytile=ytile, zoom=zoom)
            except IntegrityError:
                return OSMTile.get_data(xtile, ytile, zoom)
            
            # Try to get the file from the OSM tile server
            try:
                response = urllib.urlopen(get_tile_url(xtile, ytile, zoom))
            except IOError:
                # If it fails... try again, but only once
                if retry:
                    return OSMTile.get_data(xtile, ytile, zoom, retry=False)
                else:
                    raise
            
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
    
