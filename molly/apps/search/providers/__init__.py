import logging

from molly.conf.provider import Provider
from django.core.urlresolvers import resolve, Resolver404
from django.http import Http404
from django.views.generic.simple import redirect_to


logger = logging.getLogger(__name__)

class BaseSearchProvider(Provider):
    
    def perform_search(self, request, query, application=None):
        """
        Takes a string query, an HttpRequest, and an optional application
        name. Returns a list of results. Results are dictionaries with keys
        having the meanings given in the documentation at ref/apps/search. 
        """
        
        raise NotImplementedException()

    def get_metadata(self, request, url):
        """
        Resolves the given :data:`url` to the view that would handle it and
        returns the result of calling
        :meth:`~molly.utils.views.BaseView.get_metadata` on that view, passing
        it the :data:`request`.
        
        May raise :exc:`~django.core.urlresolvers.Resolver404` or
        :exc:`~django.http.Http404`. All other exceptions will be caught and
        logged.
        """
        callback, callback_args, callback_kwargs = resolve(url)

        metadata = {}
        try:
            metadata['application'] = callback.conf.local_name
        except AttributeError, e:
            pass

        # We use redirect_to when we're supporting legacy URLs; we don't want
        # to display them in the search results.
        if callback == redirect_to:
            raise Http404

        if not hasattr(callback, 'get_metadata'):
            return metadata

        # The only exceptions we're expecting are Http404 and Resolver404, which can be dealt
        # with by the caller. We'll log any others
        try:
            get_metadata = getattr(callback, 'get_metadata')
            metadata.update(get_metadata(request, *callback_args, **callback_kwargs))
        except (Http404, Resolver404), e:
            raise
        except Exception, e:
            logger.exception("Unexpected exception raised on call to %r", get_metadata)

        return metadata

    def _perform_query_expansion(self, query):
        try:
            terms = self.conf._query_expansion_terms
        except AttributeError, e:
            terms = self.conf._query_expansion_terms = self._load_query_expansion_terms()

        query = [t for t in query.split(' ') if t]
        query = [(frozenset([t]) | terms.get(t, frozenset())) for t in query[:]]

        return query

    def _load_query_expansion_terms(self):
        """
        Loads a query expansion file using the format used by a GSA.

        See http://code.google.com/apis/searchappliance/documentation/50/help_gsa/serve_query_expansion.html#synonyms
        for more information.
        """

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

from google_search_appliance import GSASearchProvider
from application_search import ApplicationSearchProvider
