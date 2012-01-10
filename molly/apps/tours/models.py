from django.db import models
from django.core.urlresolvers import reverse

from molly.utils.i18n import languages_to_try

from molly.apps.places.models import Entity

class Tour(models.Model):
    
    name = models.TextField()
    stops = models.ManyToManyField(Entity, through='StopOnTour')
    type = models.SlugField()
    
    def get_absolute_url(self):
        return reverse('tours:tour-start', args=[self.id])
    
    def __unicode__(self):
        return self.name


class StopOnTour(models.Model):
    
    tour = models.ForeignKey(Tour)
    entity = models.ForeignKey(Entity)
    order = models.IntegerField()
    
    class Meta:
        ordering = ['order']
    
    def get_absolute_url(self):
        return reverse('tours:tour', args=[self.tour.id, self.order])
    
    @property
    def description(self):
        
        descriptions = self.entity.metadata.get('tours', {}).get(self.tour.type, {})
        for language in languages_to_try():
            if language in descriptions:
                return descriptions[language]
        return None

