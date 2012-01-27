from django.conf.urls.defaults import *

from views import PageView

urlpatterns = patterns('',
    (r'^$', PageView, { 'page':'index' }, 'index'),
    (r'^(?P<page>[a-zA-Z0-9\-]+)/$',
        PageView, {}, 'page'),
)
