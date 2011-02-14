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

# This used to be its own app, but has now been subsumed into the 'Maps' app,
# but we use the old app_label on the models for backwards compatibility

def get_generated_map_dir():
    return getattr(settings,
                   'GENERATED_MAP_DIR',
                   os.path.join(settings.CACHE_DIR, 'generated_maps'))

def get_marker_dir():
    return getattr(settings,
                   'MARKER_DIR',
                   os.path.join(settings.CACHE_DIR, 'markers'))

def get_osm_tile_dir():
    return getattr(settings,
                   'OSM_TILE_DIR',
                   os.path.join(settings.CACHE_DIR, 'osm_tiles'))

class GeneratedMap(models.Model):
    """
    In database representation of a generated map on disk
    """
    
    hash = models.CharField(max_length=16, unique=True, primary_key=True)
    generated = models.DateTimeField()
    last_accessed = models.DateTimeField()
    _metadata = models.TextField(blank=True)
    faulty = models.BooleanField(default=False)
    
    class Meta:
        app_label = 'maps'
        db_table = 'osm_generatedmap'

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
        """
        When deleting from the db, also delete on disk
        """
        try:
            os.unlink(self.get_filename())
        except:
            pass
        return super(GeneratedMap, self).delete(*args, **kwargs)

def get_tile_url(xtile, ytile, zoom):
    """
    Return a URL for a tile given some OSM tile co-ordinates
    """
    return "http://tile.openstreetmap.org/%d/%d/%d.png" % (zoom, xtile, ytile)

class OSMTile(models.Model):
    """
    In-database representation of a cached OSM tile on disk
    """
    
    xtile = models.IntegerField()
    ytile = models.IntegerField()
    zoom = models.IntegerField()
    last_fetched = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (('xtile', 'ytile', 'zoom'),)
        app_label = 'maps'
        db_table = 'osm_osmtile'

    def get_filename(self):
        osm_tile_dir = get_osm_tile_dir()
        if not os.path.exists(osm_tile_dir):
            os.mkdir(osm_tile_dir)
        return os.path.join(osm_tile_dir, "%d-%d-%d.png" % (self.xtile, self.ytile, self.zoom))

    def refresh_data(self, retry=True):
            
        # Try to get the file from the OSM tile server
        try:
            response = urllib.urlopen(get_tile_url(self.xtile, self.ytile, self.zoom))
        except IOError:
            # If it fails... try again, but only once
            if retry:
                return self.refresh_data(retry=False)
            else:
                raise
        
        s = StringIO()
        s.write(response.read())
        f = open(self.get_filename(), 'w')
        f.write(s.getvalue())
        f.close()
        s.seek(0)
        return s

    @staticmethod
    def get_data(xtile, ytile, zoom):
        """
        Fetch an OSM tile from the OSM tile server, and cache it if necessary.
        """
        try:
            osm_tile = OSMTile.objects.get(xtile=xtile, ytile=ytile, zoom=zoom, last_fetched__gt = datetime.now() - timedelta(1))
            if osm_tile.last_fetched < datetime.now() - timedelta(weeks=1):
                try:
                    return osm_tile.refresh_data()
                except IOError:
                    # Ignore IOErrors, because we already have some data, so
                    # just use that
                    pass
            return open(osm_tile.get_filename())
        except (OSMTile.DoesNotExist, IOError):
            try:
                osm_tile, created = OSMTile.objects.get_or_create(xtile=xtile, ytile=ytile, zoom=zoom)
            except IntegrityError:
                return OSMTile.get_data(xtile, ytile, zoom)
            
            return osm_tile.refresh_data()
    
class OSMUpdate(models.Model):
    """
    A user-submitted update to OSM 
    """
    
    contributor_name = models.TextField(blank=True)
    contributor_email = models.TextField(blank=True)
    contributor_attribute = models.BooleanField()

    entity = models.ForeignKey(Entity)    
    
    submitted = models.DateTimeField(auto_now_add=True)
    
    old = models.TextField()
    new = models.TextField()
    
    notes = models.TextField(blank=True)
    
    approved = models.BooleanField(default=False)
    
    class Meta:
        app_label = 'maps'
        db_table = 'osm_osmupdate'
    
