import logging

from django.core.urlresolvers import resolve
from django.http import Http404

logger = logging.getLogger('molly.apps.search.providers')

class BaseSearchProvider(object):
    
    def perform_search(self, request, query, application=None):
        """
        Takes a string query, an HttpRequest, and an optional application
        name. Returns a list of results. Results are dictionaries with keys
        having the meanings given in the documentation at ref/apps/search. 
        """
        
        raise NotImplementedException()

    def get_metadata(self, request, url):
        # This may raise Resolver404 - let the caller deal with it.        
        callback, callback_args, callback_kwargs = resolve(url)

        if not hasattr(callback, 'get_metadata'):
            return {}

        # The only exception we're expecting is Http404, which can be dealt
        # with by the caller. We'll log any others
        try:
            get_metdata = getattr(callback, 'get_metadata')
            return get_metadata(self.request, *callback_args, **callback_kwargs)
        except Http404:
            raise
        except Exception, e:
            logger.exception("Unexpected exception raised on call to %s.get_metadata" % callback.__name__)
            return {}

    def _perform_query_expansion(self, query):
        try:
            terms = self.conf._query_expansion_terms
        except AttributeError, e:
            terms = self.conf._query_expansion_terms = self._load_query_expansion_terms()

        query = [t for t in query.split(' ') if t]
        print query
        print terms
        query = [(frozenset([t]) | terms.get(t, frozenset())) for t in query[:]]

        return query

    def _load_query_expansion_terms(self):
        if hasattr(self.conf, 'query_expansion_file'):
            f = open(self.conf.query_expansion_file)
            terms = {}
            for line in f.readlines():
                line = line.replace('\n', '')
                line = line.split('#')[0].strip()
                if not line:
                    continue
                elif '=' in line or '>' in line:
                    (term, equivs), op = (line.split('='), '=') if '=' in line else (line.split('>'), '>')
                    term, equivs = term.strip(), [e.strip() for e in equivs.split(',')]
                    terms[term] = terms.get(term, frozenset()) | frozenset(equivs)
                    if op == '>':
                        for equiv in equivs:
                            terms[equiv] = terms.get(term, frozenset()) | frozenset([term])
                elif line.startswith('{') and line.endswith('}'):
                    equivs = frozenset([e.strip() for e in line[1:-1].split(',')])
                    for equiv in equivs:
                        terms[equiv] = terms.get(equiv, frozenset()) | (equivs - frozenset([equiv]))
                else:
                    raise ValueError('Malformed query expansion file')

            return terms
        else:
            return {}