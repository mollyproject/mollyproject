import logging
from urllib2 import urlopen
from lxml import etree
from datetime import datetime, timedelta, date, time
import socket
socket.setdefaulttimeout(5)

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from molly.conf.provider import Provider, task
from molly.apps.weather.models import (
    Weather, PTYPE_OBSERVATION, PTYPE_FORECAST)

logger = logging.getLogger(__name__)


METOFFICE_OUTLOOK_CHOICES = (
    ('NA', 'unk'),
    (0, 'cs'),
    (1, 's'),
    (2, 'pc'),     # night
    (3, 'si'),
    (4, 'unk'),    # DUST ??
    (5, 'm'),
    (6, 'f'),
    (7, 'gc'),     # Medium-level cloud
    (8, 'gc'),     # Low-level cloud
    (9, 'lrs'),    # night
    (10, 'lrs'),
    (11, 'd'),
    (12, 'lr'),
    (13, 'hr'),   # Heavy rain shower (night)??
    (14, 'hr'),   # Heavy rain shower (day)??
    (15, 'hr'),
    (16, 'hr'),   # Sleet shower (night)??
    (17, 'hr'),   # Sleet shower (day)??
    (18, 'hr'),   # Sleet??
    (19, 'h'),   # Hail shower (night)
    (20, 'h'),   # Hail shower (day)
    (21, 'h'),   # Hail
    (22, 'lsn'),   # Light snow shower (night)
    (23, 'lsn'),   # Light snow shower (day)
    (24, 'lsn'),   # Light snow
    (25, 'hsn'),   # Heavy snow shower (night)
    (26, 'hsn'),   # Heavy snow shower (day)
    (27, 'hsn'),   # Heavy snow
    (28, 'tsh'),   # Thundery shower (night)
    (29, 'tsh'),   # Thundery shower (day)
    (30, 'tst'),   # Thunder storm
    (31, 'tst'),   # Tropical storm
    (32, 'unk'),   # NOT USED?
    (33, 'h'),   # Haze
    )

BASE_METOFFICE_URL = "http://datapoint.metoffice.gov.uk/public/data/val"


class MetOfficeProvider(Provider):
    """
    Scrapes MetOffice DataPoint / observations API
    Documentation is available at: http://www.metoffice.gov.uk/public/ddc/datasets-documentation.html#DailyForecast
    TODO: this class should be splitted in two (observations and forecasts).
    """

    ATTRIBUTION = {
        'title': _('MetOffice'),
        'url': _('http://www.metoffice.gov.uk/')
    }

    FRESHNESS = timedelta(hours=3)

    def __init__(self, forecasts_location_id, observations_location_id):
        self.forecasts_location_id = forecasts_location_id
        self.observations_location_id = observations_location_id

    def fetch_observation(self):
        return Weather.objects.get(location_id=self.observations_location_id,
            ptype=PTYPE_OBSERVATION)

    def fetch_forecasts(self):
        return Weather.objects.filter(
            location_id=self.forecasts_location_id, ptype=PTYPE_FORECAST,
            observed_date__gte=datetime.now().date()
        ).order_by('observed_date')

    @task(run_every=timedelta(minutes=15), default_retry_delay=2, max_retries=3)
    def import_forecasts(self, **metadata):
        api = ApiWrapper()
        forecasts, location = api.get_daily_forecasts_by_location(self.forecasts_location_id)
        for fc in forecasts:
            f = forecasts[fc]
            forecast, created = Weather.objects.get_or_create(
                    location_id=self.forecasts_location_id,
                    observed_date=fc,
                    ptype=PTYPE_FORECAST)
            forecast.name = location['name']
            forecast.min_temperature = float(f['Night']['Nm'])
            forecast.max_temperature = float(f['Day']['Dm'])
            outlooks = dict(METOFFICE_OUTLOOK_CHOICES)
            forecast.outlook = outlooks[int(f['Day']['W'])]
            forecast.observed_date = datetime.combine(fc, time(hour=0))
            forecast.save()

    @task(run_every=timedelta(minutes=15), default_retry_delay=2, max_retries=3)
    def import_observation(self, **metadata):
        api = ApiWrapper()
        observations, location = api.get_observations_by_location(self.observations_location_id)
        latest_day = sorted(observations)[-1]
        latest_hour = sorted(observations[latest_day], key=lambda x: int(x))[-1]
        latest = observations[latest_day][latest_hour]
        observation, created = Weather.objects.get_or_create(
            location_id=self.observations_location_id,
            ptype=PTYPE_OBSERVATION)
        observation.name = location['name']
        observation.temperature = float(latest['T'])
        observation.wind_speed = int(latest['S'])
        observation.wind_direction = latest['D']
        observation.pressure = int(latest['P'])
        observation.observed_date = datetime.combine(latest_day,
                time(int(latest_hour)/60))
        outlooks = dict(METOFFICE_OUTLOOK_CHOICES)
        observation.outlook = outlooks[int(latest['W'])]
        #observation.humidity = not available
        #observation.pressure_state = not available
        observation.save()

    @task(run_every=timedelta(hours=1))
    def delete_old_forecasts(self, **metadata):
        delete_until = datetime.now() - timedelta(days=2)
        logger.debug('Deleting old weather objects until %s' % delete_until)
        Weather.objects.filter(observed_date__lte=delete_until).delete()

class ApiWrapper(object):
    """
    Scrape the XML API
    """

    FORECAST_FRAGMENT_URL = '/wxfcs/all/xml'

    OBSERVATIONS_FRAGMENT_URL = '/wxobs/all/xml'

    def get_daily_forecasts_by_location(self, location_id):
        url = '{0}{1}/{2}?res=daily&key={3}'.format(BASE_METOFFICE_URL,
                self.FORECAST_FRAGMENT_URL, location_id, settings.API_KEYS['metoffice'])
        logger.debug('MetOffice: %s' % url)
        content = urlopen(url).read()
        return self.scrape_xml(content)

    def get_observations_by_location(self, location_id):
        url = '{0}{1}/{2}?res=hourly&key={3}'.format(
            BASE_METOFFICE_URL,
            self.OBSERVATIONS_FRAGMENT_URL,
            location_id,
            settings.API_KEYS['metoffice']
        )
        logger.debug('MetOffice: %s' % url)
        content = urlopen(url).read()
        return self.scrape_xml(content)

    def scrape_xml(self, content):
        """
        Scrape XML from MetOffice DataPoint API.
        Can be used to parse Forecasts/Daily, Forecasts/3hourly, Observations
        Returns a list of representations, information about the location
        """
        xml = etree.fromstring(content)
        location = xml.find('.//Location')
        l = {}
        for k in location.attrib:
            l[k] = location.attrib[k]
        periods = xml.findall('.//Period')
        p = {}
        for period in periods:
            date_val = period.get('value')
            date_parsed = date(year=int(date_val[0:4]),
                month=int(date_val[5:7]), day=int(date_val[8:10]))
            p[date_parsed] = {}
            reps = period.findall('.//Rep')
            for rep in reps:
                # rep.txt represents the number of minutes since midnight
                p[date_parsed][rep.text] = {}
                # set of attributes depends on type forecasts vs. observations,
                # but also if it's a forecast for the day or night (e.g. min temperature is
                # only available for a night forecast...
                for k in rep.attrib:
                    p[date_parsed][rep.text][k] = rep.attrib[k]
        return p, l
