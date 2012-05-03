from molly.conf.provider import Provider


class BaseGeolocationProvider(Provider):

    
    def reverse_geocode(self, lon, lat):
        return []
        
    
    def geocode(self, query):
        return []

from cloudmade import CloudmadeGeolocationProvider
from places import PlacesGeolocationProvider
