class BaseGeolocationProvider(object):

    
    def reverse_geocode(self, lon, lat):
        return []
        
    
    def geocode(self, query):
        return []

from cloudmade import CloudmadeGeolocationProvider
from places import PlacesGeolocationProvider