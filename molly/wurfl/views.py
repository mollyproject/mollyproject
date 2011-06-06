from pywurfl.algorithms import DeviceNotFound

from django.http import Http404
from django.utils.translation import ugettext as _

from molly.utils.views import BaseView
from molly.utils.breadcrumbs import *
from molly.utils.http import MediaType

from molly.wurfl.vsm import vsa
from molly.wurfl import device_parents
from molly.wurfl.wurfl_data import devices

class IndexView(BaseView):
    @BreadcrumbFactory
    def breadcrumb(self, request, context):
        return Breadcrumb(
            self.conf.local_name,
            None,
            _('Device detection'),
            lazy_reverse('index'),
        )
    
    def handle_GET(self, request, context):
        if not getattr(self.conf, 'expose_view', False):
            raise Http404
        ua = request.GET.get('ua', request.META.get('HTTP_USER_AGENT', ''))
        ua = ua.decode('ascii', 'ignore')

        try:
            device = devices.select_ua(
                ua,
                search=vsa
            )
        except (KeyError, DeviceNotFound):
            device = devices.select_id('generic_xhtml')

        accepts = self.parse_accept_header(request.META.get('HTTP_ACCEPT', ''))
        renderers = MediaType.resolve(accepts, self.FORMATS_BY_MIMETYPE)
        formats = [renderer.format for renderer in renderers]

        context.update({
            'id': device.devid,
            'is_mobile': not 'generic_web_browser' in device_parents[device.devid],
            'brand_name': device.brand_name,
            'model_name': device.model_name,
            'ua': ua,
            'matched_ua': device.devua,
            'accept': request.META.get('HTTP_ACCEPT', ''),
            'formats': formats
        })

        if request.GET.get('capabilities') == 'true':
            context['capabilities'] = dict((k, getattr(device, k)) for k in dir(device) if (not k.startswith('_') and not k.startswith('dev') and not k in ('groups','children')))

        return self.render(request, context, 'wurfl/index')
