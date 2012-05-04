import threading
from lxml import etree
import logging
import socket
socket.setdefaulttimeout(5)
from urllib2 import urlopen
from lxml.etree import tostring
from itertools import chain

from molly.apps.places.models import Route, EntityType
from molly.apps.places.providers import BaseMapsProvider

logger = logging.getLogger(__name__)


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
                    list(chain(*([c.text, tostring(c), c.tail] for c in messages.getchildren()))) +
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
