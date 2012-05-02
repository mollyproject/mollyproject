from molly.conf.provider import Provider

class BaseLibrarySearchProvider(Provider):
    """
    Abstract class implementing the interface for a provider for the library app
    """
    
    def library_search(self, query):
        """
        @param query: The query to be performed
        @type query: molly.apps.library.models.
        @return: A list of results
        @rtype: [LibrarySearchResult]
        """
        pass
    
    def control_number_search(self, control_number):
        """
        @param control_number: The unique ID of the item to be looked up
        @type control_number: str
        @return: The item with this control ID, or None
        @rtype: LibrarySearchResult
        """
        pass

from z3950 import Z3950

class BaseMetadataProvider(Provider):
    """
    Abstract class implementing the interface for a provider which fetches
    book covers
    """
    
    def annotate(self, books):
        """
        @param books: The books to be annotated
        @type books: [LibrarySearchResult]
        @rtype: None
        """
        pass

from google import GoogleBooksProvider
