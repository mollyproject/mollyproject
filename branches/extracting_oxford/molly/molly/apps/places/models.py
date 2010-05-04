import simplejson

from math import atan2, degrees

from django.contrib.gis.db import models
from django.core.urlresolvers import reverse
from django.contrib.gis.geos import Point

class Source(models.Model):
    module_name = models.CharField(max_length=128)
    name = models.CharField(max_length=128)
    last_updated = models.DateTimeField(auto_now=True)
    
IDENTIFIER_SCHEME_PREFERENCE = ('atco', 'oxpoints', 'osm', 'naptan')



class EntityType(models.Model):
    slug = models.SlugField()
    article = models.CharField(max_length=2)
    verbose_name = models.TextField()
    verbose_name_plural = models.TextField()
    show_in_nearby_list = models.BooleanField()
    show_in_category_list = models.BooleanField()
    note = models.TextField(null=True)

    subtype_of = models.ManyToManyField('self', blank=True, symmetrical=False, related_name="subtypes")
    subtype_of_completion = models.ManyToManyField('self', blank=True, symmetrical=False, related_name="subtypes_completion")

    def __unicode__(self):
        return self.verbose_name
        
    def save(self, *args, **kwargs):
        super(EntityType, self).save(*args, **kwargs)
        print "Saved et"

        subtypes_of = set([self])
        for subtype_of in self.subtype_of.all():
            subtypes_of |= set(subtype_of.subtype_of_completion.all())

        if set(self.subtype_of_completion.all()) != subtypes_of:
            self.subtype_of_completion = subtypes_of
            for et in self.subtypes.all():
                et.save()
            for e in self.entities_completion.all():
                e.save()
        else:
            super(EntityType, self).save(*args, **kwargs)
            

    class Meta:
        ordering = ('verbose_name',)

class Identifier(models.Model):
    scheme = models.CharField(max_length=32)
    value = models.CharField(max_length=256)

class Entity(models.Model):
    title = models.TextField(blank=True)
    source = models.ForeignKey(Source)
    
    primary_type = models.ForeignKey(EntityType, null=True)
    all_types = models.ManyToManyField(EntityType, blank=True, related_name='entities')
    all_types_completion = models.ManyToManyField(EntityType, blank=True, related_name='entities_completion')

    location = models.PointField(srid=4326, null=True)
    geometry = models.GeometryField(srid=4326, null=True)
    _metadata = models.TextField(default='{}')

    absolute_url = models.TextField()

    parent = models.ForeignKey('self', null=True)
    is_sublocation = models.BooleanField(default=False)
    is_stack = models.BooleanField(default=False)
    
    _identifiers = models.ManyToManyField(Identifier)
    identifier_scheme = models.CharField(max_length=32)
    identifier_value = models.CharField(max_length=256)
    
    @property
    def identifiers(self):
        try:
            return self.__identifiers
        except AttributeError:
            self.__identifiers = dict((i.scheme, i.value) for i in self._identifiers.all())
            return self.__identifiers

    def get_metadata(self):
        try:
            return self.__metadata
        except AttributeError:
            self.__metadata = simplejson.loads(self._metadata)
            return self.__metadata
    def set_metadata(self, metadata):
        self.__metadata = metadata
    metadata = property(get_metadata, set_metadata)

    COMPASS_POINTS = ('N','NE','E','SE','S','SW','W','NW')
    def get_bearing(self, p1):
        p2 = self.location
        lat_diff, lon_diff = p2[0] - p1[0], p2[1] - p1[1]
        return self.COMPASS_POINTS[int(((90 - degrees(atan2(lon_diff, lat_diff))+22.5) % 360) // 45)]
        
    def get_distance_and_bearing_from(self, point):
        if point is None or not self.location:
            return None, None
        if not isinstance(point, Point):
            point = Point(point, srid=4326)
        return (
            point.transform(27700, clone=True).distance(self.location.transform(27700, clone=True)),
            self.get_bearing(point),
        )

    def save(self, *args, **kwargs):
        try:
            self._metadata = simplejson.dumps(self.__metadata)
        except AttributeError:
            pass

        identifiers = kwargs.pop('identifiers', None)
        if not identifiers is None:            
            self.absolute_url = self._get_absolute_url(identifiers)

        super(Entity, self).save(*args, **kwargs)
            
        if not identifiers is None:
            self._identifiers.all().delete()
            id_objs = []
            for scheme, value in identifiers.items():
                id_obj = Identifier(scheme=scheme, value=value)
                id_obj.save()
                id_objs.append(id_obj)
            self._identifiers.add(*id_objs)
        
        self.update_all_types_completion()
        
    def update_all_types_completion(self):    
        all_types = set()
        for t in self.all_types.all():
            all_types |= set(t.subtype_of_completion.all())
        if set(self.all_types_completion.all()) != all_types:
            self.all_types_completion = all_types
                
    def delete(self, *args, **kwargs):
        for identifier in self._identifiers.all():
            identifier.delete()
        super(Entity, self).delete()

    objects = models.GeoManager()


    class Meta:
        ordering = ('title',)

    def _get_absolute_url(self, identifiers):
        for scheme in IDENTIFIER_SCHEME_PREFERENCE:
            if scheme in identifiers:
                self.identifier_scheme, self.identifier_value = scheme, identifiers[scheme]
                return reverse('maps:entity', args=[scheme, identifiers[scheme]])
        raise AssertionError
    
    def get_absolute_url(self):
        return self.absolute_url

    def __unicode__(self):
        return self.title

    @property
    def display_id(self):
        if self.entity_type.slug == 'postcode':
            return getattr(self, self.entity_type.id_field).strip()
        else:
            return getattr(self, self.entity_type.id_field)
            
    def simplify_for_render(self, simplify_value, simplify_model):
        return simplify_value({
            '_type': '%s.%s' % (self.__module__[:-7], self._meta.object_name),
            '_pk': self.pk,
            '_url': self.get_absolute_url(),
            'location': self.location,
            'parent': simplify_model(self.parent, terse=True),
            'all_types': [simplify_model(t, terse=True) for t in self.all_types_completion.all()],
            'primary_type': simplify_model(self.primary_type, terse=True),
            'metadata': self.metadata,
            'title': self.title,
            'identifiers': self.identifiers,
        })
            


