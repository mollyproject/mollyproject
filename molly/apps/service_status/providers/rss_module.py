from molly.conf.provider import Provider
from datetime import datetime
import dateutil.parser
import feedparser

class RSSModuleServiceStatusProvider(Provider):
    def __init__(self, name, slug, url):
        self.name, self.slug, self.url = name, slug, url

    def parse_date(self, s):
        try:
            return dateutil.parser.parse(s)
        except (TypeError, ValueError):
            return None

    def safe_parse(self, f, s):
        try:
            return f(s)
        except (TypeError, ValueError):
            return None

    def get_status(self):
        services_feed = feedparser.parse(self.url)
        
        try:
            lastBuildDate = self.parse_date(services_feed.entries[0].get('ss_lastchecked'))
        except IndexError, e:
            try:
                lastBuildDate = self.parse_date(services_feed.headers['last-modified'])
            except Exception, e:
                lastBuildDate = None
            
        
        services = []
        for service in services_feed.entries:
            services.append({
                'source': self.slug,
                'source_name': self.name,
                'name': service.title,

                'responding': {'true':True,'false':False}.get(service.get('ss_responding')),
                'lastChecked': self.parse_date(service.get('ss_lastchecked')),
                'lastSeen': self.parse_date(service.get('ss_lastseen')),
                'availability': self.safe_parse(int, service.get('ss_availability')),
                'averageResponseTime': self.safe_parse(float, service.get('ss_averageresponsetime')),
                'statusMessage': service.get('ss_statusmessage'),
            })
            services[-1]['status'] = {0: 'down', 100: 'up', None: {True: 'up', False: 'down', }.get(services[-1]['responding'], 'unknown')}.get(services[-1]['availability'], 'partial')
            
        return {
            'services': services,
            'lastBuildDate': lastBuildDate,
        }

    def get_announcements(self):
        return []
