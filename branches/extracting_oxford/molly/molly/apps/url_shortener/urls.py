from django.conf.urls.defaults import *

from views import IndexView, ShortenURLView, ShortenedURLRedirectView

urlpatterns = patterns('',
    (r'^$',
        IndexView, {},
        'index'),

    (r'^shorten_url/$',
        ShortenURLView, {},
        'shorten'),
    (r'^(?P<slug>[0-9][0-9A-Za-z]*)/?$',
        ShortenedURLRedirectView, {},
        'redirect'),
)
