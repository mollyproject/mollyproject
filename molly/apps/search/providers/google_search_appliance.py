import urllib
import urllib2
import logging
import re

import xml.etree
import xml.parsers.expat

from lxml import etree

from django.http import Http404
from django.core.urlresolvers import Resolver404, reverse

from molly.apps.search.providers import BaseSearchProvider

logger = logging.getLogger(__name__)

class GSASearchProvider(BaseSearchProvider):

    SCHEME_HOST_RE = re.compile(r'[a-z\d]+:\/\/[a-z.\-\d]+\/')

    def __init__(self, search_url, domain, params={}, title_clean_re=None):
        self.search_url, self.domain, self.params = search_url, domain, params
        self.title_clean_re = re.compile(title_clean_re) if title_clean_re else None

    def perform_search(self, request, query, application=None):

        if application:
            domain = self.domain + reverse('%s:index' % application)[:-1]
        else:
            domain = self.domain

        query = self._perform_query_expansion(query)
        query = ' '.join(('(%s)' % (' OR '.join(((('"%s"' % t) if ' ' in t else t) for t in terms))) for terms in query[:]))

        params = dict(self.params)
        params.update({
            'q': query.encode('utf-8'),
            'output': 'xml',
            'ie': 'utf8',
            'oe': 'utf8',
            'as_sitesearch': domain,
        })

        try:
            response = urllib2.urlopen('?'.join((self.search_url, urllib.urlencode(params))))
        except urllib2.HTTPError, e:
            logger.exception("Couldn't fetch results from Google Search Appliance")
            return []

        try:
            xml_root = etree.parse(response)
        except xml.parsers.expat.ExpatError, e:
            logger.exception("Couldn't parse results from Google Search Appliance")
            return []

        results = []

        for result in xml_root.findall('.//RES/R'):
            # Retrieve the URL and chop off the scheme and host parts, leaving
            # just the local part.
            url = result.find('U').text
            url = self.SCHEME_HOST_RE.sub('/', url)

            title = result.find('T').text
            try:
                title = self.title_clean_re.match(title).group(1)
            except AttributeError:
                pass

            metadata = {
                'url': url,
                'excerpt': (result.find('S').text or '').replace('<br>', ''),
                'title': title,
            }

            try:
                metadata.update(self.get_metadata(request, url))
            except (Resolver404, Http404):
                continue

            results.append(metadata)

        return results
        