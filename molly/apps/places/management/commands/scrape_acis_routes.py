from string import ascii_lowercase
from urllib2 import urlopen
from lxml import etree
import logging

from django.core.management.base import BaseCommand, CommandError
from django.http import Http404

from molly.apps.places import get_entity
from molly.apps.places.models import Route, StopOnRoute, Entity, Source
from molly.apps.places.providers.naptan import NaptanMapsProvider
from molly.utils.i18n import set_name_in_language

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    args = '<ACIS_URL ...>'
    help = 'URL to the ACIS Live instance to scrape'

    SEARCH_PAGE = '%s/web/public_service.asp?service=%s&web_search=1'

    def handle(self, *args, **options):
        
        # Searching can flag up the same results again and again, so store
        # which ones we've found
        found_routes = set()
        
        for url in args:
            
            # Try and find all bus routes in the system
            for term in list(ascii_lowercase) + map(str, range(0,9)):
                found_routes = self._scrape_search(
                    url, self.SEARCH_PAGE % (url, term), found_routes)
            
            # Now try and find buses that don't exist on that system any more
            for route in Route.objects.filter(external_ref__startswith=url):
                if route.external_ref not in found_routes:
                    logger.info('Remove route not found on system: %s', route)
                    route.delete()
    
    def _scrape_search(self, url, search_page, found_routes):
        results = etree.parse(urlopen(search_page), parser = etree.HTMLParser())
        for tr in results.find('.//table').findall('tr')[1:]:
            try:
                service, operator, destination = tr.findall('td')
            except ValueError:
                pass
            else:
                service = service.text
                operator = operator.text
                link = url + destination[0].attrib['href']
                destination = destination[0].text
                if link not in found_routes:
                    found_routes.add(link)
                    route, created = Route.objects.get_or_create(
                        external_ref=link,
                        defaults={
                            'service_id': service,
                            'operator': operator,
                            'service_name': destination,
                        }
                    )
                    if not created:
                        route.service_id = service
                        route.operator = operator
                        route.service_name = destination
                        route.save()
                    self._scrape(route, link)
        
        return found_routes
    
    def _scrape(self, route, url):
        print route
        url += '&showall=1'
        service = etree.parse(urlopen(url), parser = etree.HTMLParser())
        route.stops.clear()
        for i, tr in enumerate(service.find('.//table').findall('tr')[1:]):
            
            try:
                stop_code = tr[1][0].text
            except IndexError:
                
                # Stops on ACIS Live that don't have codes, e.g., out of county
                # stops
                stop_name = tr[3][0].text
                try:
                    entity = Entity.objects.get(source=self._get_source(),
                                                _identifiers__scheme='acisroute',
                                                _identifiers__value=stop_name)
                except Entity.DoesNotExist:
                    entity = Entity(source=self._get_source())
                
                entity_type = self._get_entity_type()
                entity.primary_type = entity_type
                identifiers = { 'acisroute': stop_name }
                entity.save(identifiers=identifiers)
                set_name_in_language(entity, 'en', title=stop_name)
                entity.all_types = (entity_type,)
                entity.update_all_types_completion()
            
            else:
                # TODO: Change identifier lookup based on ACIS region
                try:
                    entity = get_entity('naptan', stop_code)
                    if entity.source == self._get_source():
                        # Raise Http404 if this is a bus stop we came up with,
                        # so any name changes, etc, get processed
                        raise Http404()
                except Http404:
                    # Out of zone bus stops with NaPTAN codes - alternatively,
                    # the fake bus stops Oxontime made up for the TUBE route
                    try:
                        entity = Entity.objects.get(source=self._get_source(),
                                                    _identifiers__scheme='naptan',
                                                    _identifiers__value=stop_code)
                    except Entity.DoesNotExist:
                        entity = Entity(source=self._get_source())
                    identifiers = { 'naptan': stop_code }
                    entity_type = self._get_entity_type()
                    entity.primary_type = entity_type
                    entity.save(identifiers=identifiers)
                    set_name_in_language(entity, 'en', title=tr[3][0].text)
                    entity.all_types = (entity_type,)
                    entity.update_all_types_completion()
                    entity.save()
                
            StopOnRoute.objects.create(route=route, entity=entity, order=i)
    
    def _get_source(self):
        source, created = Source.objects.get_or_create(module_name=__name__,
                                                       name='ACIS Route Scraper')
        return source
    
    def _get_entity_type(self):
        return NaptanMapsProvider(None)._get_entity_types()['BCT']
