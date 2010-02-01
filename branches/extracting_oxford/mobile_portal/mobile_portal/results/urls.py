from django.conf.urls.defaults import *

from views import IndexView

urlpatterns = patterns('mobile_portal.results.views',
   (r'^$', IndexView, {}, 'results_index'),
)