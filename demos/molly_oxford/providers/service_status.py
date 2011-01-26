import feedparser
import dateutil.parser

class OUCSStatusProvider(object):
    name = 'Computing Services'
    slug = 'oucs'

    _STATUS_URL = 'http://status.ox.ac.uk/verboserss.php'
    _ANNOUNCE_URL = 'http://status.ox.ac.uk/oxitems/generatersstwo2.php?channel_name=oucs/status-announce'
    
    def parse_date(self, s):
        try:
            return dateutil.parser.parse(s)
        except (TypeError, ValueError):
            return None
            
    def get_status(self):
        services_feed = feedparser.parse(self._STATUS_URL)

        services = []
        lastBuildDate = self.parse_date(services_feed.feed.lastbuilddate)
        
        for service in services_feed.entries:


            services.append({
                'source': self.slug,
                'source_name': self.name,
                'name': service.title,

                'lastChecked': None,
                'lastSeen': None,
                'availability': None,
                'averageResponseTime': None,
                'statusMessage': service.get('description'),
                'status': self.get_category(service.category),
            })

        services[-1]['responding'] = services[-1]['status'] in ('partial','up')

        return { 'services': services , 'lastBuildDate': lastBuildDate }

    def get_announcements(self):
        return feedparser.parse(self._ANNOUNCE_URL).entries

    def get_category(self, name):
        """
        Normalises status names to a set we can have icons for.
        """
        #return random.choice(('up', 'down', 'partial', 'unknown'))
        name = (name or '').lower()
        if name in ('up', 'down', 'partial', 'unknown'):
            return name
        elif name == 'Web interface is not responding':
            return 'unknown'
        else:
            return 'unknown'

