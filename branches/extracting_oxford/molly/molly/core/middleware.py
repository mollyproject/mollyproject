from django.conf import settings
from molly.utils import geolocation

from molly.wurfl.wurfl_data import devices
from molly.wurfl import device_parents
from pywurfl.algorithms import DeviceNotFound
from molly.wurfl.vsm import VectorSpaceAlgorithm

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
        if 'HTTP_X_SKYFIRE_PHONE' in request.META:
            request.browser = devices.select_id('generic_skyfire')
            skyfire_device = request.META['HTTP_X_SKYFIRE_PHONE']
            request.device = devices.select_ua(
                skyfire_device,
                search=LocationMiddleware.vsa
            )
            try:
                request.device.resolution_width, request.device.resolution_height = \
                    map(int, request.META['HTTP_X_SKYFIRE_SCREEN'].split(','))[2:4]
            except (KeyError, ValueError):
                pass
        else:
            request.device = request.browser
            
        request.map_width = min(320, request.device.resolution_width-10)
        request.map_height = min(320, request.device.resolution_height-10)
        

