import urllib, urllib2, re
from django.core.urlresolvers import reverse, Resolver404, RegexURLResolver
from django.conf import settings
from django.http import Http404
from xml.etree import ElementTree as ET

"""\
Provides support for searching the site using the Google Search Appliance
(GSA) and then augmenting each result with metadata. We also look in each of
the installed apps for a callable search.SiteSearch, which is able to return
further results to be prepended to those returned by the GSA.

Each result is a dictionary containing the following keys:

url:
    The local part of the URL for the page, ordinarily returned by the GSA
application:
    The module that handles the URL
excerpt:
    The relevant bit of the page as returned by the GSA. SiteSearch may set
    this to an appropriate HTML string, or the empty string otherwise.
additional:
    More information about the resource represented at the URL. For example,
    the maps application returns the type of entity and a distance from the
    user's location.
title:
    The page title, as returned by the GSA (sans any 'm.ox |'). Applications
    may override this if they desire.
redirect_if_sole_result:
    A boolean, default False, which will cause the search page to redirect to
    the URL if only one result is returned.
category:
    Not used for display, but could probably be used for grouping results.
    Currently set by the podcasts app.
    
For each result returned by the GSA we resolve the URL into a view callable,
and call its get_metadata method if it exists. get_metadata must return a
dictionary, which is then used to update the information returned by the GSA.
""" 

GOOGLE_SEARCH_URL = 'http://googlesearch.oucs.ox.ac.uk/search?%s'

class OverrideResponse(Exception):
    pass

class GoogleSearch(object):
    def __init__(self, domain, application, query, request=None):
        self.domain = domain
        self.application = application
        self.query = query
        self.request = request
        
        self.results, self.overrides, redirect = self.check_applications()
        
        if redirect:
            raise OverrideResponse(redirect)

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
        
        print urllib2.urlopen(GOOGLE_SEARCH_URL % urllib.urlencode({
            'as_sitesearch': self.domain,
            'client': 'oxford',
            'Go':'Go!',
            'q': self.query.encode('utf8'),
            'output': 'xml',
            'ie': 'utf8',
            'oe': 'utf8',
        })).read()
        
        resolver = RegexURLResolver(r'^/', settings.ROOT_URLCONF)

        SCHEME_HOST_RE = re.compile(r'[a-z\d]+:\/\/[a-z.\-\d]+\/')
        
        for result in self.results:
            yield result

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
            
            if metadata['application'] in self.overrides:
                continue

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

    def check_applications(self):
        if self.application:
            applications = [settings.PORTAL_APPS[self.application]]
        else:
            applications = settings.INSTALLED_APPS
            
        all_results, overrides, redirects = [], set(), set()
            
        for app in applications:
            print "Searching", app
            try:
                site_search_name = '%s.search' % app
                _temp = __import__(site_search_name,
                                   globals(), locals(),
                                   ['SiteSearch'], -1)
                print dir(_temp)
                if not hasattr(_temp, 'SiteSearch'):
                    raise ImportError
            except ImportError:
                continue
            else:
                site_search = _temp.SiteSearch
                
            print "Found searcher"
            
            results, override, redirect = site_search(
                self.query,
                app == self.application,
                self.request
            )
            
            all_results += results
            if override:
                overrides.add(app)
            if redirect:
                redirects.add(redirect)
        
        redirect = redirects.pop() if len(redirects) == 1 else None

        return all_results, overrides, redirect