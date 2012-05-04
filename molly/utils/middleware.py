import sys
import logging

from collections import namedtuple
from django.http import Http404
from django.conf import settings
from django.contrib.gis.geos import Point
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.middleware.locale import LocaleMiddleware
from django.utils import translation
from django.core.signals import got_request_exception

from molly.utils.views import handler500

logger = logging.getLogger(__name__)

Location = namedtuple('Location', ['point', 'accuracy'])

class LocationMiddleware(object):
    """
    Adds a user_location attribute to requests where the user's location
    can be determined by any of a number of means (query string parameters,
    HTTP header, previously set session variable, etc)
    
    user_location is a namedtuple of (point, accuracy). user_location.point
    is a django.contrib.gis.geos.Point object using SRID 4326
    """
    def process_request(self, request):
        latitude = None
        longitude = None
        accuracy = None

        # If the request has latitude and longitude query params, use those
        if 'latitude' in request.GET and 'longitude' in request.GET:
            latitude = request.GET['latitude']
            longitude = request.GET['longitude']
            accuracy = request.GET.get('accuracy')

        # Else look for an X-Current-Location header with the format
        # X-Current-Location: latitude=0.0,longitude=0.0,accuracy=1
        elif 'HTTP_X_CURRENT_LOCATION' in request.META:
            location_string = request.META['HTTP_X_CURRENT_LOCATION']
            try:
                temp_dict = dict([token.split('=') for token in location_string.split(',')])
                if 'latitude' in temp_dict and 'longitude' in temp_dict:
                    latitude = temp_dict['latitude']
                    longitude = temp_dict['longitude']
                    accuracy = temp_dict.get('accuracy')
            except ValueError:
                # Malformed X-Current-Location header (e.g. latitude=0.0&foo)
                pass
                
        # Else use a geolocation:location session variable
        elif 'geolocation:location' in request.session:
            longitude, latitude = request.session['geolocation:location']
            accuracy = request.session.get('geolocation:accuracy')

        if latitude and longitude:
            point = Point(float(longitude), float(latitude), srid=4326)
            if accuracy:
                accuracy = float(accuracy)
            else:
                accuracy = None
            request.user_location = Location(point, accuracy)

class ErrorHandlingMiddleware(object):
    def process_exception(self, request, exception):
        if isinstance(exception, Http404):
            return
        elif isinstance(exception, PermissionDenied):
            return
        elif isinstance(exception, ImproperlyConfigured):
            logger.critical("Site improperly configured", exc_info=True)
        else:
            logger.exception("[500] %s at %s" % (type(exception).__name__, request.path))
            got_request_exception.send(sender=self, request=request)
            return handler500(request, exc_info=sys.exc_info())

class CookieLocaleMiddleware(LocaleMiddleware):
    
    def process_request(self, request):
        
        language_code = request.REQUEST.get('language_code')
        
        if language_code and language_code in dict(settings.LANGUAGES):
            translation.activate(language_code)
        
        else:
            
            if hasattr(request, 'session'):
                # MOLLY-177: Force using cookies to set language
                session = request.session
                del request.session
                super(CookieLocaleMiddleware, self).process_request(request)
                request.session = session
                
            else:
                
                super(CookieLocaleMiddleware, self).process_request(request)
    
    def process_response(self, request, response):
        
        language_code = request.REQUEST.get('language_code')
        if language_code and language_code in dict(settings.LANGUAGES):
            response.set_cookie(settings.LANGUAGE_COOKIE_NAME, language_code)
        
        return super(CookieLocaleMiddleware, self).process_response(request,
                                                                    response)

