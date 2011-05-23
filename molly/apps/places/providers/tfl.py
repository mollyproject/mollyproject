from urllib2 import urlopen
from xml.dom import minidom
from collections import defaultdict
import threading

from molly.apps.places.providers import BaseMapsProvider

class TubeRealtimeProvider(BaseMapsProvider):
    """
    Populates tube station entities with real-time departure information
    """
    
    TRACKERNET_STATUS_URL = 'http://cloud.tfl.gov.uk/TrackerNet/StationStatus'
    TRACKERNET_PREDICTION_URL = 'http://cloud.tfl.gov.uk/TrackerNet/PredictionDetailed/%s/%s'
    
    def get_statuses(self):
        statuses = {}
        xml = minidom.parseString(urlopen(self.TRACKERNET_STATUS_URL).read())
        for stationstatus in xml.getElementsByTagName('StationStatus'):
            name = stationstatus.getElementsByTagName('Station')[0].getAttribute('Name')
            status = stationstatus.getElementsByTagName('Status')[0].getAttribute('Description')
            status += ' ' + stationstatus.getAttribute('StatusDetails')
            statuses[name] = status
        return statuses
    
    def augment_metadata(self, entities, **kwargs):
        threads = []
        
        for entity in filter(lambda e: e.primary_type.slug == 'tube-station', entities):
            
            # Try and match up entity with StationStatus name
            for station, status in self.get_statuses().items():
                if entity.title.startswith(station):
                    entity.metadata['real_time_information'] = {
                        'pip_info': [status] if status != 'Open ' else [],
                    }
            if 'real_time_information' not in entity.metadata:
                entity.metadata['real_time_information'] = {}
            
            if 'london-underground-identifiers' in entity.metadata:
                thread = threading.Thread(target=self.get_times, args=[entity])
                thread.start()
                threads.append(thread)
        
        for thread in threads:
            thread.join()
    
    def get_times(self, entity):
        
        services = []
        
        for line, station in entity.metadata['london-underground-identifiers']:
            next_info = defaultdict(list)
            
            xml = minidom.parseString(urlopen(self.TRACKERNET_PREDICTION_URL % (line, station)).read())
            for tag in xml.getElementsByTagName('T'):
                next_info[tag.getAttribute('Destination')].append(int(tag.getAttribute('SecondsTo')))
            
            line_name = xml.getElementsByTagName('LineName')[0].childNodes[0].nodeValue[:-5]
            
            for dest, eta in next_info.items():
                services.append({
                    'service': line_name,
                    'destination': dest,
                    'etas': eta
                })
        
        services.sort(key=lambda s: s['etas'][0])
        for service in services:
            etas = [round(e/60) for e in service['etas']]
            etas = ['DUE' if e == 0 else '%d mins' % e for e in etas]
            service['next'] = etas[0]
            service['following'] = etas[1:]
        entity.metadata['real_time_information']['services'] = services
        entity.metadata['meta_refresh'] = 30