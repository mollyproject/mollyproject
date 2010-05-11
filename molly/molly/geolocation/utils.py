from functools import wraps

from molly.conf import get_app

from models import Geocode

__all__ = ['geocode', 'reverse_geocode']

def _cached(getargsfunc):
    def g(f):
        @wraps(f)
        def h(*args, **kwargs):
            args = getargsfunc(*args, **kwargs)
            app = get_app('molly.geolocation', args.pop('local_name', None))
            try:
                return Geocode.recent.get(local_name=app.local_name, **args).results
            except Geocode.DoesNotExist:
                pass
            results = f(providers=app.providers, **args)
            
            geocode, _ = Geocode.objects.get_or_create(local_name = app.local_name,
                                                       **args)
            geocode.results = results
            geocode.save()
            
            return results
        return h
    return g

@_cached(lambda query,local_name=None:{'query':query, 'local_name':local_name})
def geocode(query, providers):
    results = []
    for provider in providers:
         results += provider.geocode(query)
    return results

@_cached(lambda lon,lat,local_name=None:{'lon': lon, 'lat':lat, 'local_name':local_name})
def reverse_geocode(lon, lat, providers):
    results = []
    for provider in providers:
         results += provider.reverse_geocode(lon, lat)
    return results
    
