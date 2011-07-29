import logging
from itertools import chain

import simplejson

from molly.geolocation.providers import BaseGeolocationProvider
from molly.apps.places.models import Entity, EntityName

logger = logging.getLogger(__name__)

class PlacesGeolocationProvider(BaseGeolocationProvider):
    def __init__(self, search_identifiers = None):
        self.search_identifiers = search_identifiers

    def geocode(self, query):
        entities = Entity.objects.all()
        if self.search_identifiers:
            entities = entities.filter(
                _identifiers__scheme__in = self.search_identifiers,
                _identifiers__value__iexact = query,
                location__isnull = False
            )
        else:
            entities = entities.filter(
                _identifiers__value__iexact = query,
                location__isnull = False
            )

        entities = chain(
            Entity.objects.filter(names__title__iexact = query,
                                  location__isnull = False),
            entities,
        )

        for entity in entities:
            yield {
                'name': entity.title,
                'location': tuple(entity.location),
                'accuracy': 100,
            }