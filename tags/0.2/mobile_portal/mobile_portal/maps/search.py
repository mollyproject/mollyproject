import re, simplejson, urllib2

from django.core.urlresolvers import reverse

from views import EntityDetailView
from mobile_portal.oxpoints.models import Entity


class SiteSearch(object):
    POSTCODE_RE = re.compile('OX\d{1,2} ?\d[A-Z]{2}')
    OUCSCODE_RE = re.compile('[A-Z]{4}')

    def __new__(cls, query, only_app, request):
        return (
            cls.busstops(query, only_app, request)
          + cls.postcodes(query, only_app, request)
          + cls.oucscodes(query, only_app, request)
        ), False, None

    @classmethod
    def postcodes(cls, query, only_app, request):
        if not cls.POSTCODE_RE.match(query.upper()):
            return []

        query = query.upper().replace(' ', '')

        try:
            entity = Entity.objects.get(entity_type__slug='postcode', post_code=query)
        except Entity.DoesNotExist:
            return []

        metadata = {
            'redirect_if_sole_result': True,
            'url': reverse('maps_entity_nearby_list', args=['postcode',query]),
            'excerpt': '',
            'application': 'maps',
        }

        return [metadata]

    @classmethod
    def busstops(cls, query, only_app, request):

        id = query.strip()
        if len(id) == 5: 
            id = '693' + id
        if len(id) == 2:
            entities = Entity.objects.filter(central_stop_id=id.upper())
        elif len(id) == 8:
            entities = Entity.objects.filter(naptan_code=id)
        else:
            entities = []


        results = []
        for entity in entities:
            metadata = EntityDetailView.get_metadata(
                request,
                entity.entity_type.slug,
                entity.display_id
            )

            result = {
                'redirect_if_sole_result': True,
                'url': entity.get_absolute_url(),
                'excerpt': '', 
                'application': 'maps',
            }
            result.update(metadata)

            results.append(result)

        return results

    @classmethod
    def oucscodes(cls, query, only_app, request):
        if not cls.OUCSCODE_RE.match(query.upper()):
            return []

        json = simplejson.load(urllib2.urlopen(
            'http://m.ox.ac.uk/oxpoints/oucs:%s.json' % query.lower()))

        results = []
        for result in json:
            try:
                entity = Entity.objects.get(oxpoints_id=result['uri'][-8:])
            except Entity.DoesNotExist:
                continue

            metadata = EntityDetailView.get_metadata(request, entity.entity_type.slug, entity.display_id)

            metadata.update({
                'redirect_if_sole_result': True,
                'url': entity.get_absolute_url(),
                'application': 'maps',
            })

            results.append(metadata)
        return results

