from django.conf import settings
import geolocation

from mobile_portal.wurfl.wurfl_data import devices
from mobile_portal.wurfl import device_parents
from pywurfl.algorithms import JaroWinkler

OPERA_DEVICES = {
    'Nokia # E71': 'nokia_e71_ver1'
}

class LocationMiddleware(object):
    def process_request(self, request):

        if 'location' in request.session:
            request.location = request.session['location']
            request.placemark = request.session.get('placemark')
        else:
            request.location = None
            request.placemark = None
            
        request.device = devices.select_ua(
            request.META['HTTP_USER_AGENT'],
            search=JaroWinkler(accuracy=0.85)
        )

        # Opera Mini sends a header with better device information
        
        #raise Exception(device_parents[request.device.devid])
        if 'opera_mini_ver1' in device_parents[request.device.devid]:
            opera_device = request.META.get('HTTP_X_OPERAMINI_PHONE')
            opera_devid = OPERA_DEVICES.get(opera_device)
            if opera_devid:
                request.device = devices.select_id(opera_devid)
#        if any((x in request.META['HTTP_USER_AGENT']) for x in ['Firefox', 'IE', 'Iceweasel', 'Safari', 'Opera', 'Chrome']):
#            request.device.max_image_width=800 