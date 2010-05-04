from math import atan2, degrees
from django.shortcuts import get_object_or_404
from django.contrib.gis.geos import Point

from models import EntityType, Entity, Identifier

def get_entity(scheme, value):
    return get_object_or_404(Entity, _identifiers__scheme=scheme, _identifiers__value=value)


def is_favourite(request, entity):
    return entity.pk in request.session.get('maps:favourites', ())

def make_favourite(request, entity, value):
    if not 'maps:favourites' in request.session:
        request.session['maps:favourites'] = []
    if value and not is_favourite(request, entity):
        request.session['maps:favourites'].insert(0, entity.pk)
    elif not value and is_favourite(request, entity):
        request.session['maps:favourites'].remove(entity.pk)
    request.session.modified = True

COMPASS_POINTS = ('N','NE','E','SE','S','SW','W','NW')
def get_bearing(p1, p2):
    lat_diff, lon_diff = p2[0] - p1[0], p2[1] - p1[1]
    return COMPASS_POINTS[int(((90 - degrees(atan2(lon_diff, lat_diff))+22.5) % 360) // 45)]

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
