import re
import simplejson
import urllib2
from itertools import chain

from django.core.urlresolvers import reverse
from django.db.models import Q
from django.utils.translation import ugettext as _

from views import NearbyDetailView, EntityDetailView
from models import Entity, EntityType


class ApplicationSearch(object):

    def __init__(self, conf):
        self.conf = conf

    def perform_search(self, request, query, is_single_app_search):
        return chain(
            self.nearby_search(request, query, is_single_app_search),
            self.entity_search(request, query, is_single_app_search),
            self.entity_type_search(request, query, is_single_app_search),
        )

    def nearby_search(self, request, query, is_single_app_search):
        """
        nearby_search was invented to allow a user to query in plain text such
        e.g. 'post boxes near OUCS' this is yet to be completed."
        """
        # TODO: Complete
        query = query.lower().split(_(' near '))
        if len(query) != 2:
            return []

        return []

    def entity_search(self, request, query, is_single_app_search):
        entities = Entity.objects.all()
        if hasattr(self.conf, 'search_identifiers'):
            entities = entities.filter(
                _identifiers__scheme__in = self.conf.search_identifiers,
                _identifiers__value__iexact = query,
            )
        else:
            entities = entities.filter(
                _identifiers__value__iexact = query,
            )

        entities = chain(
            Entity.objects.filter(title__iexact = query),
            entities,
        )

        for entity in entities:
            result = {
                'url': entity.get_absolute_url(),
                'application': self.conf.local_name,
                'redirect_if_sole_result': True,
            }
            result.update(EntityDetailView(self.conf).get_metadata(request, entity.identifier_scheme, entity.identifier_value))
            yield result

    def entity_type_search(self, request, query, is_single_app_search):
        entity_types = EntityType.objects.filter(
            Q(verbose_name__iexact = query) | Q(verbose_name_plural__iexact = query))

        for entity_type in entity_types:
            result = {
                'url': reverse('places:nearby-detail', args=[entity_type.slug]),
                'application': self.conf.local_name,
                'redirect_if_sole_result': True,
            }
            result.update(NearbyDetailView(self.conf).get_metadata(request, entity_type.slug))
            yield result
