class BaseLibrarySearchProvider:
    """
    Abstract class implementing the interface for a provider for the library app
    """
    
    def library_search(self, query):
        """
        @param query: The query to be performed
        @return: A list of results
        @rtype: [LibrarySearchResult]
        """
        pass

from z3950 import Z3950