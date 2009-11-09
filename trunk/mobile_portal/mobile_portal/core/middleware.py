from django.conf import settings
import geolocation

from mobile_portal.wurfl.wurfl_data import devices
from mobile_portal.wurfl import device_parents
from pywurfl.algorithms import JaroWinkler, DeviceNotFound

OPERA_DEVICES = {
    'Nokia # E71': 'nokia_e71_ver1'
}

class LocationMiddleware(object):
    def process_request(self, request):
        ua = request.META.get('HTTP_USER_AGENT', '')

        try:
            request.device = devices.select_ua(
                request.META['HTTP_USER_AGENT'],
                search=JaroWinkler(accuracy=0.85)
            )
        except (KeyError, DeviceNotFound):
            request.device = devices.select_id('generic_xhtml')

        if 'MSIE' in ua and not 'IEMobile' in ua:
            if 'MSIE 4.0' in ua:
                request.device = devices.select_id('msie40_generic')
            elif 'MSIE 5.0' in ua:
                request.device = devices.select_id('msie50_generic')
            elif 'MSIE 6.0' in ua:
                request.device = devices.select_id('msie60_generic')
            else:
                request.device = devices.select_id('msie70_generic')
        if 'T-Mobile G1 Build' in ua:
            request.device = devices.select_id('tmobile_g1_ver1')
        elif 'HTC Hero' in ua:
            request.device = devices.select_id('tmobile_g1_ver1')
        elif 'Android' in ua:
            request.device = devices.select_id('tmobile_g1_ver1')
        
        if "generic_web_browser" in device_parents[request.device.devid]:
            request.device.max_image_width = 320
            request.device.max_image_height = 320

        # Opera Mini sends a header with better device information
        
        #raise Exception(device_parents[request.device.devid])
        if 'opera_mini_ver1' in device_parents[request.device.devid]:
            opera_device = request.META.get('HTTP_X_OPERAMINI_PHONE')
            opera_devid = OPERA_DEVICES.get(opera_device)
            if opera_devid:
                request.device = devices.select_id(opera_devid)
#        if any((x in request.META['HTTP_USER_AGENT']) for x in ['Firefox', 'IE', 'Iceweasel', 'Safari', 'Opera', 'Chrome']):
#            request.device.max_image_width=800

from django.db import connection

class PrintQueriesMiddleware(object):
    def process_response(self, request, response):
        for query in connection.queries:
            print '-'*80
            print query['sql']
        return response