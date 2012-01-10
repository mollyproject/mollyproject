from math import atan2, degrees
import re

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
    elif hasattr(request, 'user_location'):
        point = request.user_location.point
    else:
        point = None
    return point

def bus_route_sorter(route):
    start_nums = re.match('([0-9]+)([A-Z]?)', route)
    letter_nums = re.match('([A-Z]+)([0-9]+)([A-Z]?)', route)
    if start_nums:
        return int(start_nums.group(1)), start_nums.group(2)
    elif letter_nums:
        return letter_nums.group(1), int(letter_nums.group(2)), letter_nums.group(2)
    else:
        return route
