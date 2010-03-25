class BaseSearchProvider(object):
    
    def perform_search(cls, query, request, application=None):
        """
        Takes a string query, an HttpRequest, and an optional application
        name. Returns a list of results. Results are dictionaries with keys
        having the meanings given in the documentation at ref/apps/search. 
        """
        
        raise NotImplementedException()
