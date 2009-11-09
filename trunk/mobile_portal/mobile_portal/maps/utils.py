from math import atan2, degrees
from django.shortcuts import get_object_or_404
from mobile_portal.oxpoints.models import EntityType, Entity

def get_entity(type_slug, id):
    entity_type = get_object_or_404(EntityType, slug=type_slug)
    id_field = str(entity_type.id_field)
    return get_object_or_404(Entity, **{id_field: id, 'entity_type': entity_type})

def entity_ref(entity):
    return (entity.entity_type.slug, entity.display_id)

def is_favourite(request, entity):
    return entity_ref(entity) in request.preferences['maps']['favourites']
    
def make_favourite(request, entity, value):
    if value and not is_favourite(request, entity):
        request.preferences['maps']['favourites'].insert(0, entity_ref(entity))
    elif not value and is_favourite(request, entity):
        request.preferences['maps']['favourites'].remove(entity_ref(entity))
        
COMPASS_POINTS = ('N','NE','E','SE','S','SW','W','NW')
def get_bearing(p1, p2):
    lat_diff, lon_diff = p2[0] - p1[0], p2[1] - p1[1]
    return COMPASS_POINTS[int(((90 - degrees(atan2(lon_diff, lat_diff))+22.5) % 360) // 45)]
