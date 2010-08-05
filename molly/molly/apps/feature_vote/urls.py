from django.conf.urls.defaults import *

from .views import IndexView, IdeaDetailView

urlpatterns = patterns('',
    (r'^$', IndexView, {}, 'index'),
    (r'^(?P<id>\d+)/$', IdeaDetailView, {}, 'idea-detail'),
)
