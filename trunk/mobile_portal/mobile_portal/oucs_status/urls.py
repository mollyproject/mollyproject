from django.conf.urls.defaults import *

from views import IndexView

urlpatterns = patterns('mobile_portal.oucs_status.views',
   (r'^$', IndexView, {}, 'oucs_status_index'),
)
