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