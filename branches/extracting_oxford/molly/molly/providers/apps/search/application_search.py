from molly.apps.search.providers import BaseSearchProvider

class ApplicationSearchProvider(BaseSearchProvider):
    def __init__(self, application_names=None):
        self.application_names = application_names
        self.applications = None
        
    def perform_search(self, request, query, application=None):
        if self.applications == None:
            self.find_applications()
        
        return []
        
    def find_applications(self):
        pass
        
