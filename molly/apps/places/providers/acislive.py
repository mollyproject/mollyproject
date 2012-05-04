import threading
from datetime import datetime, timedelta
from lxml import etree
import re
import logging
from string import ascii_lowercase
import socket
socket.setdefaulttimeout(5)
from urllib2 import urlopen

from django.db import transaction, reset_queries, connection
from django.http import Http404

from molly.apps.places.models import Route, StopOnRoute, Entity, Source, EntityType
from molly.apps.places.providers import BaseMapsProvider
from molly.apps.places import get_entity
from molly.apps.places.providers.naptan import NaptanMapsProvider
from molly.utils.i18n import set_name_in_language
from molly.conf.provider import task

logger = logging.getLogger(__name__)

class ACISLiveMapsProvider(BaseMapsProvider):
    """
    Populates bus stop entities with real time departure metadata using the ACIS
    Live interface
    """
    
    ACISLIVE_URLS = {
        # The key is the atco regional prefix - the value is a tuple consisting
        # of the base URL for the ACIS Live instance, a function to determine
        # the identifier to use for the live bus times board, and a function to
        # determine the identifier to use for the bus stop messages board
        '010': ('http://bristol.acislive.com/',
                lambda entity: entity.identifiers.get('atco'),
                lambda entity: entity.identifiers.get('atco'),
               ), # Bristol
        '040': ('http://bucks.acislive.com/',
                lambda entity: entity.identifiers.get('atco'),
                lambda entity: entity.identifiers.get('atco'),
               ), # Buckinghamshire
        '050': ('http://www.cambridgeshirebus.info/',
                lambda entity: entity.identifiers.get('atco'),
                lambda entity: entity.identifiers.get('atco'),
               ), # Cambridgeshire
        '060': ('http://cheshire.acislive.com/',
                lambda entity: entity.identifiers.get('atco'),
                lambda entity: entity.identifiers.get('atco'),
               ), # Cheshire East
        '080': ('http://cornwall.acislive.com/',
                lambda entity: entity.identifiers.get('atco'),
                lambda entity: entity.identifiers.get('atco'),
               ), # Cornwall
        '160': ('http://gloucestershire.acislive.com/',
                lambda entity: entity.identifiers.get('atco'),
                lambda entity: entity.identifiers.get('atco'),
                ), # Gloucestershire
        '240': ('http://kent.acislive.com/',
                lambda entity: entity.identifiers.get('atco'),
                lambda entity: entity.identifiers.get('atco'),
                ), # Kent
        '250': ('http://lancashire.acislive.com/',
                lambda entity: entity.identifiers.get('atco'),
                lambda entity: entity.identifiers.get('atco'),
                ), # Lancashire
        '329': ('http://wymetro.acislive.com/',
                lambda entity: '329%05d' % int(entity.identifiers.get('plate')),
                lambda entity: '329%05d' % int(entity.identifiers.get('plate'))
               ), # York
        '340': ('http://www.oxontime.com/',
                lambda entity: entity.identifiers.get('naptan'),
                lambda entity: entity.identifiers.get('atco'),
               ), # Oxfordshire
        '370': ('http://sypte.acislive.com/',
                lambda entity: entity.identifiers.get('atco')[:3] + entity.identifiers.get('atco')[4:],
                lambda entity: entity.identifiers.get('atco')[:3] + entity.identifiers.get('atco')[4:],
                ), # South Yorkshire
        '440': ('http://westsussex.acislive.com/',
                lambda entity: entity.identifiers.get('atco'),
                lambda entity: entity.identifiers.get('atco'),
                ), # Wessex
        '450': ('http://wymetro.acislive.com/',
                lambda entity: entity.identifiers.get('plate'),
                lambda entity: entity.identifiers.get('plate'),
               ), # West Yorkshire
        '450': ('http://swindon.acislive.com/',
                lambda entity: entity.identifiers.get('atco'),
                lambda entity: entity.identifiers.get('atco'),
               ), # Swindon
        '571': ('http://cardiff.acislive.com/',
                lambda entity: entity.identifiers.get('atco'),
                lambda entity: entity.identifiers.get('atco'),
               ), # Cardiff
    }
    
    def get_acislive_base(self, entity):
        """
        Gets the ACIS live information for this entity
        
        @return: A tuple of base URL, identifier for realtime info, identifier
                 for messages
        """
        
        if entity.identifiers.get('naptan', '').startswith('272'):
            # Made up Oxontime codes
            return ('http://www.oxontime.com/',
                    entity.identifiers.get('naptan'), None)
        
        if entity.identifiers.get('atco', '')[:3] in self.ACISLIVE_URLS:
            base, departures, messages = self.ACISLIVE_URLS[entity.identifiers['atco'][:3]]
            return base, departures(entity), messages(entity)
        else:
            raise NoACISLiveInstanceException
    
    def get_realtime_url(self, entity):
        """
        Gets the appropriate URL for the realtime departure board for that
        entity.
        
        @return: A string of the URL for that stop departure board, or None if
                 there is no known departure board for that stop
        """
        base, departures, messages = self.get_acislive_base(entity)
        return base + 'pip/stop.asp?naptan=%s&textonly=1' % departures
    
    def get_messages_url(self, entity):
        """
        Gets the URL for the bus stop messages associated for that entity
        
        @return: A string of the URL for that stop departure board, or None if
                 there is no known messages URL for that stop
        """
        base, departures, messages = self.get_acislive_base(entity)
        if messages:
            return base + 'pip/stop_simulator_message.asp?NaPTAN=%s' % messages
        else:
            return None
        
    
    def augment_metadata(self, entities, routes=[], **kwargs):
        threads = []
        for entity in entities:
            
            bus_et = EntityType.objects.get(slug='bus-stop')
            
            if bus_et not in entity.all_types.all():
                continue
            
            thread = threading.Thread(target=self.get_times,
                                      args=[entity, routes])
            thread.start()
            threads.append(thread)
        
        for thread in threads:
            thread.join()
    
    def get_times(self, entity, routes):
        try:
            try:
                realtime_url = self.get_realtime_url(entity)
                xml = etree.parse(urlopen(realtime_url),
                                  parser = etree.HTMLParser())
            except (TypeError, IOError):
                rows = []
                pip_info = []
            except NoACISLiveInstanceException:
                return
            else:
                try:
                    cells = xml.find('.//table').findall('td')
                    rows = [cells[i:i+4] for i in range(0, len(cells), 4)]
                except AttributeError:
                    rows = []
                
                # Get the messages associated with that bus stop
                try:
                    messages_url = self.get_messages_url(entity)
                    if messages_url != None:
                        messages_page = urlopen(messages_url).read()
                        pip_info = re.findall(r'msgs\[\d+\] = "(?P<message>[^"]+)"',
                                              messages_page)
                        pip_info = filter(lambda pip: pip != '&nbsp;', pip_info)
                    else:
                        pip_info = []
                except:
                    pip_info = []
            
            services = {}
            for row in rows:
                service, destination, proximity = [row[i].text.encode('utf8').replace('\xc2\xa0', '') for i in range(3)]
                
                # Skip routes we're not interested in
                if routes and service not in routes:
                    continue
                
                # Handle scheduled departures (non-realtime)
                if ':' in proximity:
                    now = datetime.now()
                    hour, minute = map(int, proximity.split(':'))
                    diff = (datetime(now.year, now.month, now.day, hour, minute) - datetime.now()).seconds / 60
                elif proximity.lower() == 'due':
                    diff = 0
                else:
                    diff = int(proximity.split(' ')[0])
    
                if not service in services:
                    services[service] = (destination, (proximity, diff), [])
                else:
                    services[service][2].append((proximity, diff))
    
            services = [(s[0], s[1][0], s[1][1], s[1][2]) for s in services.items()]
            services.sort(key= lambda x: ( ' '*(5-len(x[0]) + (1 if x[0][-1].isalpha() else 0)) + x[0] ))
            services.sort(key= lambda x: x[2][1])
            
            services = [{
                'service': s[0],
                'destination': s[1],
                'next': s[2][0],
                'following': [f[0] for f in s[3]],
                'route': self._get_route(s[0], entity)
            } for s in services]
            
            entity.metadata['real_time_information'] = {
                'services': services,
                'pip_info': pip_info,
            }
            entity.metadata['meta_refresh'] = 30
        
        except Exception as e:
            logger.exception('Failed to get RTI from ACIS Live')
        finally:
            connection.close()
    
    def _get_route(self, service, entity):
        return Route.objects.filter(service_id=service, stops=entity).exists()

class NoACISLiveInstanceException(Exception):
    """
    An exception to indicate that there is no ACIS Live instance to determine
    real-time bus information for the passed in entity
    """
    pass

class ACISLiveRouteProvider(BaseMapsProvider):
    
    SEARCH_PAGE = '%s/web/public_service.asp?service=%s&web_search=1'

    def __init__(self, urls=None):
        """
        A list of ACIS Live URLs to scrape when importing
        """
        if urls is None:
            urls = [instance[0] for instance in ACISLiveMapsProvider.ACISLIVE_URLS.items()]
        self.urls = urls

    @task(run_every=timedelta(days=7))
    def import_data(self, **metadata):
        # Searching can flag up the same results again and again, so store
        # which ones we've found
        found_routes = set()
        
        for url in self.urls:
            
            # Try and find all bus routes in the system
            for term in list(ascii_lowercase) + map(str, range(0,9)):
                found_routes = self._scrape_search(
                    url, self.SEARCH_PAGE % (url, term), found_routes)
            
            # Now try and find buses that don't exist on that system any more
            for route in Route.objects.filter(external_ref__startswith=url):
                if route.external_ref not in found_routes:
                    logger.info('Removed route not found on system: %s', route)
                    route.delete()
    
    def _scrape_search(self, url, search_page, found_routes):
        results = etree.parse(urlopen(search_page), parser = etree.HTMLParser())
        for tr in results.find('.//table').findall('tr')[1:]:
            reset_queries()
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
                    with transaction.commit_on_success():
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
                if stop_code.startswith('693') or stop_code.startswith('272') \
                  or stop_code.startswith('734') or stop_code.startswith('282'):
                    # Oxontime uses NaPTAN code
                    scheme = 'naptan'
                elif stop_code.startswith('450'):
                    # West Yorkshire uses plate code
                    scheme = 'plate'
                else:
                    # Everyone else uses ATCO
                    scheme = 'atco'
                    if stop_code.startswith('370'):
                        # Except South Yorkshire, which mangles the code
                        stop_code = '3700%s' % stop_code[3:]
                try:
                    entity = get_entity(scheme, stop_code)
                    if entity.source == self._get_source():
                        # Raise Http404 if this is a bus stop we came up with,
                        # so any name changes, etc, get processed
                        raise Http404()
                except Http404:
                    # Out of zone bus stops with NaPTAN codes - alternatively,
                    # the fake bus stops Oxontime made up for the TUBE route
                    try:
                        entity = Entity.objects.get(source=self._get_source(),
                                                    _identifiers__scheme=scheme,
                                                    _identifiers__value=stop_code)
                    except Entity.DoesNotExist:
                        entity = Entity(source=self._get_source())
                    identifiers = {scheme: stop_code}
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
        source.save()
        return source
    
    def _get_entity_type(self):
        return NaptanMapsProvider(None)._get_entity_types()['BCT'][0]

