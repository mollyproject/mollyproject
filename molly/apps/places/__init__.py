from math import atan2, degrees
from django.shortcuts import get_object_or_404
from django.contrib.gis.geos import Point

from models import EntityType, Entity, Identifier

def get_entity(scheme, value):
    return get_object_or_404(Entity,
                             _identifiers__scheme=scheme,
                             _identifiers__value=value)

class EntityCache(dict):
    
    def __missing__(self, key):
        scheme, value = key.split(':')
        self[key] = get_entity(scheme, value)
        return self[key]

def get_point(request, entity):
    if entity and entity.location:
        point = entity.location
    elif entity and not entity.location:
        point = None
    elif request.session.get('geolocation:location'):
        point = Point(request.session.get('geolocation:location'), srid=4326)
    else:
        point = None
    return point
