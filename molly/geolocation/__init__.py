from functools import wraps
import logging

from django.conf import settings
from django.contrib.gis.geos import Point

from molly.conf import get_app
from molly.utils import haversine
from molly.geolocation.models import Geocode

__all__ = ['geocode', 'reverse_geocode']

logger = logging.getLogger(__name__)
    
def _cached(getargsfunc):
    def g(f):
        @wraps(f)
        def h(*args, **kwargs):
            args = getargsfunc(*args, **kwargs)
            app = get_app('molly.geolocation', args.pop('local_name', None))
            try:
                geocode = Geocode.recent.get(local_name=app.local_name, **args)
                logger.debug('Found cached geocode')
                return geocode.results
            except Geocode.DoesNotExist:
                logger.debug('Geocode not found in cache')
                pass
            except Geocode.MultipleObjectsReturned:
                Geocode.recent.filter(local_name=app.local_name, **args).delete()
            results = f(providers=app.providers, **args)

            i = 0
            while i < len(results):
                loc, name = Point(results[i]['location']), results[i]['name']
                if any((r['name'] == name and haversine(Point(r['location']), loc) < 100) for r in results[:i]):
                    results[i:i+1] = []
                else:
                    i += 1
            
            if hasattr(app, 'prefer_results_near'):
                point = Point(app.prefer_results_near[:2])
                distance = app.prefer_results_near[2]
                filtered_results = [
                    result for result in results if
                        haversine(Point(result['location']), point) <= distance]
                if filtered_results:
                    results = filtered_results

            try:
                geocode, created = Geocode.objects.get_or_create(
                    local_name=app.local_name, **args)
            except Geocode.MultipleObjectsReturned:
                Geocode.objects.filter(local_name=app.local_name, **args).delete()
                geocode, created = Geocode.objects.get_or_create(
                    local_name=app.local_name, **args)
            geocode.results = results
            geocode.save()
            
            return results
        return h
    return g

@_cached(lambda query,local_name=None: {'query':query, 'local_name':local_name})
def geocode(query, providers):
    results = []
    for provider in providers:
        results += provider.geocode(query)
    return results

@_cached(lambda lon,lat,local_name=None: {'lon': lon, 'lat':lat, 'local_name':local_name})
def reverse_geocode(lon, lat, providers):
    results = []
    for provider in providers:
        results += provider.reverse_geocode(lon, lat)
    return results

