import simplejson

from math import atan2, degrees

from django.conf import settings
from django.contrib.gis.db import models
from django.core.urlresolvers import reverse, NoReverseMatch
from django.contrib.gis.geos import Point
from django.utils.translation import get_language


class Source(models.Model):
    """
    Defines the data source of an Entity
    """

    module_name = models.CharField(max_length=128)
    name = models.CharField(max_length=128)
    last_updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.name

IDENTIFIER_SCHEME_PREFERENCE = getattr(
    settings,
    'IDENTIFIER_SCHEME_PREFERENCE',
    ('atco', 'osm', 'naptan', 'postcode', 'bbc-tpeg'))


class EntityTypeCategory(models.Model):
    """
    Defines a category for an entity type to be part of e.g. a bus stop will be
    part of the 'Transport' Entity Type Category.
    """

    name = models.TextField(blank=False)

    def __unicode__(self):
        return self.name


class EntityType(models.Model):
    """
    Defines a 'type' for each Entity. E.g. an entity could be of 'bus stop'
    Entity Type
    """

    slug = models.SlugField()
    
    def _for_language(self, field):
        try:
            return getattr(self.names.get(language_code=get_language()), field)
        except EntityTypeName.DoesNotExist:
            try:
                return getattr(self.names.get(language_code=settings.LANGUAGE_CODE), field)
            except EntityTypeName.DoesNotExist:
                if '-' in settings.LANGUAGE_CODE:
                    return getattr(self.names.get(language_code=settings.LANGUAGE_CODE.split('-')[0]), field)
                else:
                    raise
    
    @property
    def verbose_name(self):
        return self._for_language('verbose_name')
    
    @property
    def verbose_name_singular(self):
        return self._for_language('verbose_name_singular')
    
    @property
    def verbose_name_plural(self):
        return self._for_language('verbose_name_plural')
    
    show_in_nearby_list = models.BooleanField()
    show_in_category_list = models.BooleanField()
    note = models.TextField(null=True)
    category = models.ForeignKey(EntityTypeCategory)

    subtype_of = models.ManyToManyField('self', blank=True, symmetrical=False,
                                        related_name="subtypes")
    subtype_of_completion = models.ManyToManyField('self',
            blank=True, symmetrical=False, related_name="subtypes_completion")

    def __unicode__(self):
        return self.verbose_name

    def save(self, *args, **kwargs):
        super(EntityType, self).save(*args, **kwargs)
        
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

class EntityTypeName(models.Model):
    entity_type = models.ForeignKey(EntityType, related_name='names')
    language_code = models.CharField(max_length=10)
    verbose_name = models.TextField()
    verbose_name_singular = models.TextField()
    verbose_name_plural = models.TextField()
    
    class Meta:
        unique_together = ('entity_type', 'language_code')


class Identifier(models.Model):
    """
    Abstract identifier code for various identifier schemes such as ATCO, OSM,
    NaPTAN (e.g. 910GYSTRADM) etc.
    """

    scheme = models.CharField(max_length=32)
    value = models.CharField(max_length=256)

    def __unicode__(self):
        return self.scheme + ': ' + self.value


class EntityGroup(models.Model):
    """
    Used to express relationships between entities
    """
    
    @property
    def title(self):
        try:
            return self.names.get(language_code=get_language()).title
        except EntityGroupName.DoesNotExist:
            try:
                return self.names.get(language_code=settings.LANGUAGE_CODE).title
            except EntityGroupName.DoesNotExist:
                if '-' in settings.LANGUAGE_CODE:
                    return self.names.get(language_code=settings.LANGUAGE_CODE.split('-')[0]).title
                else:
                    raise

    source = models.ForeignKey(Source)
    ref_code = models.CharField(max_length=256)

    def __unicode__(self):
        return self.title


class EntityGroupName(models.Model):
    entity_group = models.ForeignKey(EntityGroup, related_name='names')
    title = models.TextField(blank=False)
    language_code = models.CharField(max_length=10)
    
    class Meta:
        unique_together = ('entity_group', 'language_code')


class Entity(models.Model):
    """
    An Entity represents a geo-spatial point with attached metadata. This
    includes all DB stored Points regardless of data source.
    """
    
    @property
    def title(self):
        try:
            return self.names.get(language_code=get_language()).title
        except EntityName.DoesNotExist:
            try:
                return self.names.get(language_code=settings.LANGUAGE_CODE).title
            except EntityName.DoesNotExist:
                if '-' in settings.LANGUAGE_CODE:
                    return self.names.get(language_code=settings.LANGUAGE_CODE.split('-')[0]).title
                else:
                    raise
    
    source = models.ForeignKey(Source)

    primary_type = models.ForeignKey(EntityType, null=True)
    all_types = models.ManyToManyField(EntityType, blank=True,
                                       related_name='entities')
    all_types_completion = models.ManyToManyField(EntityType, blank=True,
                                            related_name='entities_completion')
    
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

    groups = models.ManyToManyField(EntityGroup)

    @property
    def identifiers(self):
        try:
            return self.__identifiers
        except AttributeError:
            self.__identifiers = dict()
            for identifier in self._identifiers.all():
                scheme, value = identifier.scheme, identifier.value
                if scheme in self.__identifiers:
                    # Multi-valued list - first check if we've converted this
                    # key to a list already
                    if getattr(self.__identifiers[scheme], '__iter__', False) \
                     and not \
                     isinstance(self.__identifiers[scheme], basestring):
                        # We have, so just add it to the current list
                        self.__identifiers[scheme].append(value)
                    else:
                        # convert this into a list
                        self.__identifiers[scheme] = [
                            self.__identifiers[scheme],
                            value]
                else:
                    self.__identifiers[scheme] = value

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
    
    COMPASS_POINTS = ('N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW')

    def get_bearing(self, p1):
        """
        Returns a compass point direction from current Entity to another Point
        """
        p2 = self.location
        lat_diff, lon_diff = p2[0] - p1[0], p2[1] - p1[1]
        compass_point = int(((90 - degrees(atan2(lon_diff, lat_diff)) + 22.5)
            % 360) // 45)
        return self.COMPASS_POINTS[compass_point]

    def get_distance_and_bearing_from(self, point):
        """
        Returns a distance and compass direction from current Entity to
        another point
        """
        if point is None or not self.location:
            return None, None
        if not isinstance(point, Point):
            point = Point(point, srid=4326)
        return (
            point.transform(27700, clone=True).distance(
                self.location.transform(27700, clone=True)),
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
                if getattr(value, '__iter__', False) and \
                  not isinstance(value, basestring):
                    # Is an iterable, but not a string
                    for val in value:
                        id_obj = Identifier(scheme=scheme, value=val)
                        id_obj.save()
                        id_objs.append(id_obj)
                else:
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
            self.metadata['types'] = [t.slug for t in all_types]

    @property
    def all_types_slugs(self):
        try:
            return self.metadata['types']
        except:
            self.metadata['types'] = [t.slug
                                      for t in self.all_types_completion.all()]
            self.save()
            return self.metadata['types']

    def delete(self, *args, **kwargs):
        for identifier in self._identifiers.all():
            identifier.delete()
        super(Entity, self).delete()
    
    objects = models.GeoManager()

    def _get_absolute_url(self, identifiers):
        for scheme in IDENTIFIER_SCHEME_PREFERENCE:
            if scheme in identifiers:
                self.identifier_scheme = scheme
                self.identifier_value = identifiers[scheme]
                return reverse('places:entity',
                               args=[scheme, identifiers[scheme]])
        if len(identifiers) > 0:
            for scheme, identifier in identifiers.items():
                try:
                    url = reverse('places:entity', args=[scheme, identifier])
                except NoReverseMatch:
                    continue
                else:
                    self.identifier_scheme = scheme
                    self.identifier_value = identifier
                    return url
        raise AssertionError

    def get_absolute_url(self):
        return self.absolute_url
    
    def __unicode__(self):
        return self.title
    
    @property
    def display_id(self):
        for et in self.all_types.all():
            if et.slug == 'postcode':
                return getattr(self, et.id_field).strip()
            else:
                return getattr(self, et.id_field)

    def simplify_for_render(self, simplify_value, simplify_model):
        return simplify_value({
            '_type': '%s.%s' % (self.__module__[:-7], self._meta.object_name),
            '_pk': self.pk,
            '_url': self.get_absolute_url(),
            'location': self.location,
            'parent': simplify_model(self.parent, terse=True),
            'all_types': [simplify_model(t, terse=True)
                          for t in self.all_types_completion.all()],
            'primary_type': simplify_model(self.primary_type, terse=True),
            'metadata': self.metadata,
            'title': self.title,
            'identifiers': self.identifiers,
            'identifier_scheme': self.identifier_scheme,
            'identifier_value': self.identifier_value
        })

class EntityName(models.Model):
    entity = models.ForeignKey(Entity, related_name='names')
    title = models.TextField(blank=False)
    language_code = models.CharField(max_length=10)
    
    class Meta:
        unique_together = ('entity', 'language_code')
