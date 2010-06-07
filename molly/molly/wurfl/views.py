from pywurfl.algorithms import DeviceNotFound

from molly.utils.views import BaseView
from molly.utils.breadcrumbs import NullBreadcrumb

from molly.wurfl.vsm import vsa
from molly.wurfl import device_parents
from molly.wurfl.wurfl_data import devices

class IndexView(BaseView):
    breadcrumb = NullBreadcrumb
    
    def handle_GET(cls, request, context):
        ua = request.GET.get('ua', request.META.get('HTTP_USER_AGENT', ''))
        ua = ua.decode('ascii', 'ignore')

        try:
            device = devices.select_ua(
                ua,
                search=vsa
            )
        except (KeyError, DeviceNotFound):
            device = devices.select_id('generic_xhtml')

        context = {
            'id': device.devid,
            'is_mobile': not 'generic_web_browser' in device_parents[device.devid],
            'brand_name': device.brand_name,
            'model_name': device.model_name,
        }

        if request.GET.get('capabilities') == 'true':
            context['capabilities'] = dict((k, getattr(device, k)) for k in dir(device) if (not k.startswith('_') and not k.startswith('dev') and not k=='groups'))

        return cls.render(request, context, None)