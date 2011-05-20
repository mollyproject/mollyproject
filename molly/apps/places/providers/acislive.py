import threading, urllib
from datetime import datetime
from lxml import etree
import re

from molly.apps.places.models import EntityType
from molly.apps.places.providers import BaseMapsProvider

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
               ), # Cambridgeshire
        '050': ('http://www.cambridgeshirebus.info/',
                lambda entity: entity.identifiers.get('atco'),
                lambda entity: entity.identifiers.get('atco'),
               ), # Cambridgeshire
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
               ), #West Yorkshire
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
        if entity.identifiers['atco'][:3] in self.ACISLIVE_URLS:
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
        return base + 'pip/stop_simulator_message.asp?NaPTAN=%s' % messages
        
    
    def augment_metadata(self, entities, **kwargs):
        threads = []
        for entity in entities:
            
            bus_et = EntityType.objects.get(slug='bus-stop')
            
            if bus_et not in entity.all_types.all():
                continue
                
            thread = threading.Thread(target=self.get_times, args=[entity])
            thread.start()
            threads.append(thread)
        
        for thread in threads:
            thread.join()
    
    def get_times(self, entity):

        try:
            realtime_url = self.get_realtime_url(entity)
            xml = etree.parse(urllib.urlopen(realtime_url),
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
                    messages_page = urllib.urlopen(messages_url).read()
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
        } for s in services]
        
        entity.metadata['real_time_information'] = {
            'services': services,
            'pip_info': pip_info,
        }
        entity.metadata['meta_refresh'] = 30

class NoACISLiveInstanceException(Exception):
    """
    An exception to indicate that there is no ACIS Live instance to determine
    real-time bus information for the passed in entity
    """
    pass