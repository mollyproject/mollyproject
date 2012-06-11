import logging
from urllib2 import urlopen
from lxml import etree
from datetime import datetime, timedelta, date

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from molly.conf.providers import Provider, task
from molly.apps.weather.models import Weather
from molly.apps.weather.models import (
    Weather, OUTLOOK_CHOICES, VISIBILITY_CHOICES, PRESSURE_STATE_CHOICES,
    SCALE_CHOICES, PTYPE_OBSERVATION, PTYPE_FORECAST
    )

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
METOFFICE_VISIBILITY_CHOICES = (
    ('UN', 0),      # "Unknown", TODO missing association
    ('VP', VISIBILITY_CHOICES['vp']),
    ('PO', VISIBILITY_CHOICES['p']),
    ('MO', VISIBILITY_CHOICES['m']),
    ('GO', VISIBILITY_CHOICES['g']),
    ('VG', VISIBILITY_CHOICES['vg']),
    ('EX', VISIBILITY_CHOICES['e']),
)

BASE_METOFFICE_URL = "http://partner.metoffice.gov.uk/public/val"

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

    @task(run_every=timedelta(minutes=15))
    def import_forecasts(self, **metadata):
        api = ApiWrapper()
        forecasts = api.get_daily_forecasts_by_location(self.forecasts_location_id)

    @task(run_every=timedelta(minutes=15))
    def import_observation(self, **metadata):
        api = ApiWrapper()
        observations = api.get_observations_by_location(self.observations_location_id)
        latest_day = self.sortdict(observations)[-1]
        latest_hour = self.sortdict(latest_day)[-1]
        observation = Weather.objects.get_or_create(
            location_id=self.observations_location_id, ptype=PTYPE_OBSERVATION)
        observation.temperature = int(latest_hour['T'])
        observation.wind_speed = int(latest_hour['S'])
        observation.wind_direction = latest_hour['D']
        observation.pressure = int(latest_hour['P'])
        #observation.observed_date =
        observation.outlook = METOFFICE_OUTLOOK_CHOICES[latest_hour['W']]
        #observation.humidity = not available??
        observation.save()

    def sortdict(self, d):
        for key in sorted(d): yield d[key]


class ApiWrapper(object):
    """
    Scrape the XML API
    """

    FORECAST_FRAGMENT_URL = '/wxfcs/all/xml'

    OBSERVATIONS_FRAGMENT_URL = '/wxobs/all/xml'

    def get_daily_forecasts_by_location(self, location_id):
        content = urlopen('{0}{1}/{2}?res=daily&key={3}'.format(
            BASE_METOFFICE_URL,
            self.FORECAST_FRAGMENT_URL,
            location_id,
            settings.API_KEYS['metoffice']
        )).read()
        return self.scrape_xml(content)

    def get_observations_by_location(self, location_id):
        content = urlopen('{0}{1}/{2}?res=hourly&key={3}').format(
            BASE_METOFFICE_URL,
            self.OBSERVATIONS_FRAGMENT_URL,
            location_id,
            settings.API_KEYS['metoffice']
        ).read()
        return self.scrape_xml(content)

    def scrape_xml(self, content):
        """
        Scrape XML from MetOffice DataPoint API.
        Can be used to parse Forecasts/Daily, Forecasts/3hourly, Observations
        """
        xml = etree.fromstring(content)
        periods = xml.findall('.//Period')
        p = {}
        for period in periods:
            date_val = period.get('val')
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
        return p