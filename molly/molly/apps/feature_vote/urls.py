from django.conf.urls.defaults import *

from .views import IndexView, FeatureDetailView

urlpatterns = patterns('',
    (r'^$', IndexView, {}, 'index'),
    (r'^(?P<id>\d+)/$', FeatureDetailView, {}, 'feature-detail'),
)
