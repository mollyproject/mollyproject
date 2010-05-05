import threading, urllib
from lxml import etree

from molly.apps.places.providers import BaseMapsProvider

class OxontimeMapsProvider(BaseMapsProvider):
    OXONTIME_URL = 'http://www.oxontime.com/pip/stop.asp?naptan=%s&textonly=1'
    
    def augment_metadata(self, entities):
        threads = []
        for entity in entities:
            if not entity.identifiers.get('naptan','').startswith('693'):
                continue
                
            thread = threading.Thread(target=self.get_times, args=[entity])
            thread.start()
            threads.append(thread)
        
        for thread in threads:
            thread.join()
    
    def get_times(self, entity):

        try:
            xml = etree.parse(urllib.urlopen(self.OXONTIME_URL % entity.identifiers['naptan']), parser = etree.HTMLParser())
        except (TypeError, IOError):
            rows = []
        else:
            try:
                cells = xml.find('.//table').findall('td')
                rows = [cells[i:i+4] for i in range(0, len(cells), 4)]
            except AttributeError:
                rows = []
            try:
                pip_info = xml.find(".//p[@class='pipdetail']").text
            except:
                pip_info = None

        services = {}
        for row in rows:
            service, destination, proximity = [row[i].text.encode('utf8').replace('\xc2\xa0', '') for i in range(3)]

            if not service in services:
                services[service] = (destination, proximity, [])
            else:
                services[service][2].append(proximity)

        services = [(s[0], s[1][0], s[1][1], s[1][2]) for s in services.items()]
        services.sort(key= lambda x: ( ' '*(5-len(x[0]) + (1 if x[0][-1].isalpha() else 0)) + x[0] ))
        services.sort(key= lambda x: 0 if x[2]=='DUE' else int(x[2].split(' ')[0]))
        
        services = [{
            'service': s[0],
            'destination': s[1],
            'next': s[2],
            'following': s[3],
        } for s in services]
        
        entity.metadata['real_time_information'] = {
            'services': services,
            'pip_info': pip_info,
        }
