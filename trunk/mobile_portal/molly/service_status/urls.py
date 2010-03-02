from django.conf.urls.defaults import *

from views import IndexView

urlpatterns = patterns('mobile_portal.service_status.views',
   (r'^$', IndexView, {}, 'service_status_index'),
)
