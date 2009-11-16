from django.conf.urls.defaults import *

from views import RequestTokenReadyView

urlpatterns = patterns('',
    ('^request_token_ready/$',
        RequestTokenReadyView(), {},
        'secure_request_token_ready'),
)