from django.conf.urls.defaults import *

from views import IndexView

urlpatterns = patterns('mobile_portal.sakai.views',
   (r'^$', IndexView(), {}, 'sakai_index'),
)