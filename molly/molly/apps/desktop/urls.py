from django.conf.urls.defaults import *

from .views import (
    IndexView
)

urlpatterns = patterns('',
    (r'^((?P<page>[a-z\-]+)/)?$',
        IndexView, {},
        'index'),
)
