from django.conf.urls.defaults import *

urlpatterns = patterns('mobile_portal.results.views',
   (r'^$', 'index', {}, 'results_index'),
)