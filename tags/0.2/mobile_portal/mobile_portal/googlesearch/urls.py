from django.conf.urls.defaults import *

from views import GoogleSearchView

urlpatterns = patterns('',
    (r'^$', GoogleSearchView, {}, 'googlesearch_index'),
)