from django.conf.urls.defaults import *

from views import IndexView

urlpatterns = patterns('molly.apps.service_status.views',
   (r'^$', IndexView, {}, 'index'),
)
