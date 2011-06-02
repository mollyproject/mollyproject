import re
import simplejson
import urllib2
from itertools import chain

from django.core.urlresolvers import reverse
from django.db.models import Q
from django.utils.translation import ugettext as _

from views import NearbyDetailView, EntityDetailView
from models import Entity, EntityType, EntityName, EntityTypeName


class ApplicationSearch(object):

    def __init__(self, conf):
        self.conf = conf

    def perform_search(self, request, query, is_single_app_search):
        return chain(
            self.entity_search(request, query, is_single_app_search),
            self.entity_type_search(request, query, is_single_app_search),
        )

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
            (en.entity for en in EntityName.objects.filter(title__iexact = query)),
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
        entity_types = (etn.entity_type for etn in EntityTypeName.objects.filter(
            Q(verbose_name__iexact = query) | Q(verbose_name_plural__iexact = query)))

        for entity_type in entity_types:
            result = {
                'url': reverse('places:nearby-detail', args=[entity_type.slug]),
                'application': self.conf.local_name,
                'redirect_if_sole_result': True,
            }
            result.update(NearbyDetailView(self.conf).get_metadata(request, entity_type.slug))
            yield result
