from django.db import models

from molly.apps.places.models import Entity

class Tour(models.Model):
    
    stops = models.ManyToManyField(Entity, through='StopOnTour')

class StopOnTour(models.Model):
    
    tour = models.ForeignKey(Tour)
    entity = models.ForeignKey(Entity)
    order = models.IntegerField()
    
    class Meta:
        ordering = ['order']

