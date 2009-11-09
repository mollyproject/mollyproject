import simplejson
from django.contrib.gis.db import models
from django.core.urlresolvers import reverse

class EntityType(models.Model):
    slug = models.SlugField()
    article = models.CharField(max_length=2)
    verbose_name = models.TextField()
    verbose_name_plural = models.TextField()
    source = models.TextField()
    id_field = models.TextField()
    show_in_nearby_list = models.BooleanField()
    show_in_category_list = models.BooleanField()
    note = models.TextField(null=True)
    
    sub_types = models.ManyToManyField('self', blank=True)
        
    def __unicode__(self):
        return self.verbose_name
        
    class Meta:
        ordering = ('verbose_name',)

class Entity(models.Model):
    oxpoints_id = models.PositiveIntegerField(null=True, blank=True)
    naptan_code = models.CharField(max_length=8, null=True, blank=True)
    atco_code = models.CharField(max_length=12, null=True, blank=True)
    central_stop_id = models.CharField(max_length=2, null=True, blank=True)
    osm_id = models.CharField(max_length=16, null=True, blank=True)
    title = models.TextField(blank=True)
    entity_type = models.ForeignKey(EntityType, null=True)
    all_types = models.ManyToManyField(EntityType, blank=True, related_name='all_entities')
    location = models.PointField(srid=4326, null=True)
    geometry = models.GeometryField(srid=4326, null=True)
    _metadata = models.TextField(default='null')

    absolute_url = models.TextField()
    
    parent = models.ForeignKey('self', null=True)
    is_sublocation = models.BooleanField(default=False)
    is_stack = models.BooleanField(default=False)
    
    def get_metadata(self):
        try:
            return self.__metadata
        except:
            self.__metadata = simplejson.loads(self._metadata)
            return self.__metadata
    def set_metadata(self, metadata):
        self.__metadata = metadata
    metadata = property(get_metadata, set_metadata)
    
    def save(self, *args, **kwargs):
        try:
            self._metadata = simplejson.dumps(self.__metadata)
        except AttributeError:
            pass
        if self.entity_type:
            self.absolute_url = self._get_absolute_url()
        return super(Entity, self).save(*args, **kwargs)
    
    objects = models.GeoManager()
    
    class Meta:
        ordering = ('title',)

    def _get_absolute_url(self):
        return reverse('maps_entity', args=[self.entity_type.slug, self.display_id])
    def get_absolute_url(self):
        if not self.absolute_url:
            self.save()
        return self.absolute_url
        
    def __unicode__(self):
        return self.title

    @property
    def display_id(self):
        return getattr(self, self.entity_type.id_field)
        
class PostCode(models.Model):
    post_code = models.CharField(max_length=8)
    location = models.PointField(srid=4326, null=True)