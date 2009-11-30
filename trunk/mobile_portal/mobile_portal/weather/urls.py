from django.conf.urls.defaults import *

from views import IndexView

urlpatterns = patterns('mobile_portal.weather.views',
    (r'^$', IndexView, {}, 'weather_index'),
)

