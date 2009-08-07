import simplejson
from django.contrib.gis.db import models
from django.core.urlresolvers import reverse

class EntityType(models.Model):
    slug = models.SlugField()
    verbose_name = models.TextField()
    verbose_name_plural = models.TextField()
    source = models.TextField()
    id_field = models.TextField()
    
    def __unicode__(self):
        return self.verbose_name
        
    class Meta:
        ordering = ('source', 'verbose_name')

class Entity(models.Model):
    oxpoints_id = models.PositiveIntegerField(null=True, blank=True)
    atco_code = models.CharField(max_length=12, null=True, blank=True)
    osm_node_id = models.PositiveIntegerField(null=True, blank=True)
    title = models.TextField(blank=True)
    entity_type = models.ForeignKey(EntityType, null=True)
    location = models.PointField(srid=4326, null=True)
    _metadata = models.TextField(default='null')
    
    def get_metadata(self):
        try:
            return self.__metadata
        except:
            self.__metadata = simplejson.loads(self._metadata)
            return self.__metadata
    def set_metadata(self, metadata):
        self.__metadata = metadata
    metadata = property(get_metadata, set_metadata)
    
    def save(self, force_insert=False, force_update=False):
        try:
            self._metadata = simplejson.dumps(self.__metadata)
        except AttributeError:
            pass
        super(Entity, self).save(force_insert, force_update)
    
    objects = models.GeoManager()
    
    class Meta:
        ordering = ('title',)

    def get_absolute_url(self):
        return reverse('maps_entity', args=[self.entity_type.slug, getattr(self, self.entity_type.id_field)])
