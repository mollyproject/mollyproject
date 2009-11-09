import urllib, urllib2, re
from django.core.urlresolvers import reverse, Resolver404, RegexURLResolver
from django.conf import settings
from django.http import Http404
from xml.etree import ElementTree as ET

GOOGLE_SEARCH_URL = 'http://googlesearch.oucs.ox.ac.uk/search?%s'

class GoogleSearch(object):
    def __init__(self, domain, application, query, request=None):
        self.domain = domain
        self.application = application
        self.query = query
        self.request = request

    def __iter__(self):
        if self.application:
            self.domain += reverse('%s_index' % self.application)[:-1]

        response = urllib2.urlopen(GOOGLE_SEARCH_URL % urllib.urlencode({
            'as_sitesearch': self.domain,
            'client': 'oxford',
            'Go':'Go!',
            'q': self.query.encode('utf8'),
            'output': 'xml',
            'ie': 'utf8',
            'oe': 'utf8',
        }))

        xml = ET.parse(response)
        
        resolver = RegexURLResolver(r'^/', settings.ROOT_URLCONF)

        SCHEME_HOST_RE = re.compile(r'[a-z\d]+:\/\/[a-z.\-\d]+\/')

        for r in xml.getroot().findall('RES/R'):
            url = r.find('U').text

            url = SCHEME_HOST_RE.sub('/', url)

            try:
                callback, callback_args, callback_kwargs = resolver.resolve(url)
            except Resolver404:
                continue

            metadata = {
                'url': url,
                'excerpt': (r.find('S').text or '').replace('<br>', ''),
                'application': callback.__module__.split('.')[1],
            }

            if metadata['application'] == 'core':
                metadata['application'] = None

            if hasattr(callback, 'get_metadata'):
                try:
                    metadata.update(getattr(callback, 'get_metadata')(self.request, *callback_args, **callback_kwargs))
                except Http404:
                    continue
                    
                if metadata.get('exclude_from_search'):
                    continue
                
            else:
                title = r.find('T').text
                if title.startswith('m.ox | '):
                    title = title[7:]

                metadata .update({
                    'title': title,
                    'category': None,
                })

            yield metadata
