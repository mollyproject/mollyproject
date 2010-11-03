from django.conf.urls.defaults import *

from views import IndexView, ResultListView, ResultDetailView

urlpatterns = patterns('mobile_portal.contact.views',
    (r'^$', IndexView, {}, 'index'),
    (r'^results/$', ResultListView, {}, 'result_list'),
    (r'^results/(?P<id>[^\/]+)/$', ResultDetailView, {}, 'result_detail'),
)
