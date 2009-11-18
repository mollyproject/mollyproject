from django.conf.urls.defaults import *

urlpatterns = patterns('mobile_portal.weather.views',
    (r'^$', 'index', {}, 'weather_index'),
)

