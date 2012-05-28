import threading
import logging
import socket

from urllib2 import urlopen
from itertools import chain
from datetime import timedelta
from lxml import etree

from molly.apps.places import get_entity
from molly.apps.places.models import Route, EntityType, StopOnRoute, Source, Entity
from molly.apps.places.providers import BaseMapsProvider
from molly.apps.places.providers.naptan import NaptanMapsProvider
from molly.conf.provider import task
from molly.utils.i18n import set_name_in_language

socket.setdefaulttimeout(5)
logger = logging.getLogger(__name__)

# Maps operator encoded names to known "friendly versions"
OPERATOR_NAMES = {'SOX': 'Stagecoach',
        'TT': 'Thames Travel',
        'OBC': 'Oxford Bus Company',
        '*Voyager_PD_RAV(en-GB)*': 'ARRIVA',
        }


class CloudAmberBusRouteProvider(BaseMapsProvider):
    """Sends an empty search string to the cloudamber route search.
    This returns all routes which we can scrape to collect the
    route information.
    """
    def __init__(self, url):
        self.url = "%s/Naptan.aspx?rdExactMatch=any&hdnSearchType=searchbyServicenumber&hdnChkValue=any" % url

    @task(run_every=timedelta(days=7))
    def import_data(self, **metadata):
        logger.info("Importing Route data from %s" % self.url)
        self._scrape_search()

    def _scrape_search(self):
        """Scrapes the search page and queues tasks for scraping the results"""
        e = etree.parse(self.url, parser=etree.HTMLParser())
        rows = e.findall('.//div[@class="cloud-amber"]')[0].findall('.//table')[1].findall('tbody/tr')
        for row in rows:
            route_no, operator, dest = row.getchildren()
            route_no = route_no.text
            operator = operator.find('span').text
            operator = OPERATOR_NAMES.get(operator, operator)
            route = dest.find('a').text
            route_href = dest.find('a').get('href')
            logger.debug("Found route: %s - %s - %s" % (route_no, operator, route))
            route, created = Route.objects.get_or_create(
                external_ref=route_href,
                defaults={
                    'service_id': route_no,
                    'service_name': route,
                    'operator': operator,
                }
            )
            if created:
                logging.debug("Created new route: %s" % route.service_name)
            self._scrape_route.delay(route.id, route_href)

    def _get_entity(self, stop_code, stop_name, source, entity_type):
        """Finds a bus stop entity or creates one if it cannot be found.
        If multiple entities are found we clean them up.
        """
        scheme = 'naptan'
        try:
            entity = get_entity(scheme, stop_code)
        except:
            try:
                entity = Entity.objects.get(_identifiers__scheme=scheme,
                        _identifiers__value=stop_code)
                logger.debug("Found Entity: %s" % entity)
            except Entity.DoesNotExist:
                logger.debug("Entity does not exist: %s-%s" % (stop_code, stop_name))
                entity = Entity()
            except Entity.MultipleObjectsReturned:
                logger.warning("Multiple Entities found for : %s-%s" % (stop_code, stop_name))
                Entity.objects.filter(_identifiers__scheme=scheme,
                        _identifiers__value=stop_code).delete()
                entity = Entity()
            entity.primary_type = entity_type
            entity.source = source
            identifiers = {scheme: stop_code}
            set_name_in_language(entity, 'en', title=stop_name)
            entity.all_types = (entity_type,)
            entity.save(identifiers=identifiers)
        return entity

    @task(max_retries=1)
    def _scrape_route(self, route_id, href):
        """Load route data from our Cloudamber provider and capture the stop data."""
        logger.info("Scraping route: %s" % href)
        e = etree.parse(href, parser=etree.HTMLParser())
        rows = e.findall('.//div[@class="cloud-amber"]')[0].findall('.//table')[1].findall('tbody/tr')
        source = self._get_source()
        entity_type = self._get_entity_type()
        for i, row in enumerate(rows):
            expand, naptan, map_href, stop_name, town = row.getchildren()
            stop_code = naptan.text
            stop_name = stop_name.find('a').text
            entity = self._get_entity(stop_code, stop_name, source, entity_type)
            StopOnRoute.objects.create(route_id=route_id, entity=entity, order=i)

    def _get_source(self):
        """Create or get a reference to this provider"""
        source, created = Source.objects.get_or_create(module_name=__name__,
                name='CloudAmber Route Scraper')
        source.save()
        return source

    def _get_entity_type(self):
        """Get the Entity type for BCT - Bus/Coach/Tram stop"""
        return NaptanMapsProvider(None)._get_entity_types()['BCT'][0]

class CloudAmberBusRtiProvider(BaseMapsProvider):
    """
    Populates bus stop entities with real time departure metadata using the
    Cloud Amber interface
    An example live instance should be hosted at http://www.oxontime.com
    """

    def __init__(self, url):
        """ url is CloudAmber instance """
        self.url = url

    def get_url(self, naptan):
        """ Constructs URL containing RTI for a given naptan busstop id """
        url = "%s/Naptan.aspx?t=departure&sa=%s&dc=&ac=96&vc=&x=0&y=0&format=xhtml" % (
                self.url, naptan)
        return url

    def augment_metadata(self, entities, routes=[], **kwargs):
        """ """
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
   
    def parse_html(self, content):
        """
        Parse HTML content (Cloud Amber's HTML) from a string
        """
        services = {}
        messages = []
        try:
            xml = etree.fromstring(content, parser=etree.HTMLParser())
            # we need the second table
            cells = xml.findall('.//div[@class="cloud-amber"]')[0].findall('.//table')[1].findall('tbody/tr/td')

            # retrieved all cells, splitting every CELLS_PER_ROW to get rows
            CELLS_PER_ROW = 5
            rows = [cells[i:i+CELLS_PER_ROW] for i in range(0, len(cells), CELLS_PER_ROW)]

            for row in rows:
                service, destination, proximity = [row[i].text.encode('utf8').replace('\xc2\xa0', '') 
                        for i in range(3)]
                if proximity.lower() == 'due':
                    diff = 0
                else:
                    diff = int(proximity.split(' ')[0])

                if not service in services:
                    # first departure of this service
                    services[service] = (destination, (proximity, diff), [])
                else:
                    # following departure of this service
                    services[service][2].append((proximity, diff))

            services = [(s[0], s[1][0], s[1][1], s[1][2]) for s in services.items()]
            services.sort(key = lambda x: ( ' '*(5-len(x[0]) + (1 if x[0][-1].isalpha() else 0)) + x[0] ))
            services.sort(key = lambda x: x[2][1])

            services = [{
                'service': s[0],
                'destination': s[1],
                'next': s[2][0],
                'following': [f[0] for f in s[3]],
            } for s in services]

            # messages that can be displayed (bus stop)
            cells = xml.findall('.//table')[0].findall('tr/td')

            try:
                messages = cells[3]
                parts = ([messages.text] +
                    list(chain(*([c.text, etree.tostring(c), c.tail] for c in messages.getchildren()))) +
                    [messages.tail])
                messages = ''.join([p for p in parts if p])
                messages = [messages]
            except IndexError:
                pass
                # no message

        except Exception:
            logger.info('Unable to parse HTML', exc_info=True, extra={
                'data': {
                    'html_content': content,
                },
            })

        return services, messages

    def get_times(self, entity, routes):
        """
        Retrieve RTI information from one entity
        Get page, scrape it.
        If it fails, set the meta_refresh to get the page on
        ERROR_REFRESH_INTERVAL rather than REFRESH_INTERVAL
        Assign a route to each service if it exists in our DB.
        """
        REFRESH_INTERVAL = 30
        ERROR_REFRESH_INTERVAL = 5

        try:
            content = urlopen(self.get_url(entity.identifiers.get('naptan'))).read()
            services, messages = self.parse_html(content)
        except:
            logger.info('Unable to retrieve RTI information', exc_info=True,
                extra={
                    'data': {
                        'naptan_id': entity.identifiers.get('naptan', 0),
                    },
                })
            # if an exception occured, send empty metadata.
            entity.metadata['real_time_information'] = {
                'services': {},
                'pip_info': [],
            }
            # Get the client to refresh sooner if an exception
            entity.metadata['meta_refresh'] = ERROR_REFRESH_INTERVAL
        else:
            # Assign route to each service
            for service in services:
                service['route'] = self._get_route(service['service'], entity)

            entity.metadata['real_time_information'] = {
                'services': services,
                'pip_info': messages,
            }
            entity.metadata['meta_refresh'] = REFRESH_INTERVAL

    def _get_route(self, service, entity):
        return Route.objects.filter(service_id=service, stops=entity).exists()
