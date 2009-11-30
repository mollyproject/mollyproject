from django.conf import settings
import geolocation

from mobile_portal.wurfl.wurfl_data import devices
from mobile_portal.wurfl import device_parents
from pywurfl.algorithms import DeviceNotFound
from mobile_portal.wurfl.vsm import VectorSpaceAlgorithm

class LocationMiddleware(object):
    vsa = VectorSpaceAlgorithm(devices)
    
    def process_request(self, request):
        ua = request.META.get('HTTP_USER_AGENT', '')

        try:
            request.browser = devices.select_ua(
                request.META['HTTP_USER_AGENT'],
                search=LocationMiddleware.vsa
            )
        except (KeyError, DeviceNotFound):
            request.browser = devices.select_id('generic_xhtml')

        if 'HTTP_X_OPERAMINI_PHONE' in request.META:
            opera_device = request.META['HTTP_X_OPERAMINI_PHONE']
            request.device = devices.select_ua(
                opera_device,
                search=LocationMiddleware.vsa
            )
        else:
            request.device = request.browser
            
        request.map_width = min(320, request.device.resolution_width-10)
        request.map_height = min(320, request.device.resolution_height-10)
        

from django.db import connection

class PrintQueriesMiddleware(object):
    def process_response(self, request, response):
        for query in connection.queries:
            print '-'*80
            print query['sql']
        return response