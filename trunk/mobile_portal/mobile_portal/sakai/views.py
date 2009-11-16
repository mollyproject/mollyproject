from datetime import datetime

from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse


from mobile_portal.core.renderers import mobile_render
from mobile_portal.core.handlers import BaseView


class IndexView(BaseView):
    def handle_GET(self, request, context):
        return mobile_render(request, context, 'sakai/index')

class SakaiView(BaseView):
    def __call__(self, request, *args, **kwargs):
         access_token = request.secure_session.get('sakai_access_token')
         if not access_token:
             return self.authorize()
         
         return super(SakaiView, self).__call__(request, *args, **kwargs)
        

