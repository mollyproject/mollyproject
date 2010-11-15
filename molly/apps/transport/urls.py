from django.conf.urls.defaults import *

from views import IndexView

urlpatterns = patterns('molly.apps.transport.views',
   (r'^$', IndexView, {}, 'index'),
)
