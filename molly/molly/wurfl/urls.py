from django.conf.urls.defaults import *

from .views import IndexView

urlpatterns = patterns('',
    (r'^$', IndexView, {}, 'index'),
)

