import logging
from urllib2 import urlopen
from lxml import etree
from datetime import datetime, timedelta

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
    ('NA', OUTLOOK_CHOICES['unk']),
    (0, OUTLOOK_CHOICES['cs']),
    (1, OUTLOOK_CHOICES['s']),
    (2, OUTLOOK_CHOICES['pc']),     # night
    (3, OUTLOOK_CHOICES['si']),
    (4, OUTLOOK_CHOICES['unk']),    # DUST ??
    (5, OUTLOOK_CHOICES['m']),
    (6, OUTLOOK_CHOICES['f']),
    (7, OUTLOOK_CHOICES['gc']),     # Medium-level cloud
    (8, OUTLOOK_CHOICES['gc']),     # Low-level cloud
    (9, OUTLOOK_CHOICES['lrs']),    # night
    (10, OUTLOOK_CHOICES['lrs']),
    (11, OUTLOOK_CHOICES['d']),
    (12, OUTLOOK_CHOICES['lr']),
    (13, OUTLOOK_CHOICES['hr']),   # Heavy rain shower (night)??
    (14, OUTLOOK_CHOICES['hr']),   # Heavy rain shower (day)??
    (15, OUTLOOK_CHOICES['hr']),
    (16, OUTLOOK_CHOICES['unk']),   # Sleet shower (night)??
    (17, OUTLOOK_CHOICES['unk']),   # Sleet shower (day)??
    (18, OUTLOOK_CHOICES['unk']),   # Sleet??
    (19, OUTLOOK_CHOICES['h']),   # Hail shower (night)
    (20, OUTLOOK_CHOICES['h']),   # Hail shower (day)
    (21, OUTLOOK_CHOICES['h']),   # Hail
    (22, OUTLOOK_CHOICES['lsn']),   # Light snow shower (night)
    (23, OUTLOOK_CHOICES['lsn']),   # Light snow shower (day)
    (24, OUTLOOK_CHOICES['lsn']),   # Light snow
    (25, OUTLOOK_CHOICES['hsn']),   # Heavy snow shower (night)
    (26, OUTLOOK_CHOICES['hsn']),   # Heavy snow shower (day)
    (27, OUTLOOK_CHOICES['hsn']),   # Heavy snow
    (28, OUTLOOK_CHOICES['tsh']),   # Thundery shower (night)
    (29, OUTLOOK_CHOICES['tsh']),   # Thundery shower (day)
    (30, OUTLOOK_CHOICES['tst']),   # Thunder storm
    (31, OUTLOOK_CHOICES['tst']),   # Tropical storm
    (32, OUTLOOK_CHOICES['unk']),   # NOT USED?
    (33, OUTLOOK_CHOICES['h']),   # Haze
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

    FORECASTS_URL = "http://partner.metoffice.gov.uk/public/val/wxfcs/all/xml/%d?res=daily&key=%s"

    def __init__(self, location_id):
        self.location_id = location_id
        self.id = 'metoffice/%d' % location_id

    def fetch_observation(self):
        return Weather.objects.get(location_id=self.id,
            ptype=PTYPE_OBSERVATION)

    def fetch_forecasts(self):
        return Weather.objects.filter(
            location_id=self.id, ptype=PTYPE_FORECAST,
            observed_date__gte=datetime.now().date()
        ).order_by('observed_date')

    def scrape_forecast_daily_xml(self, content):
        xml = etree.fromstring(content)
        periods = xml.findall('.//Period')
        for period in periods:
            date = period.get('val')
            reps = period.findall('.//Rep')
            for rep in reps:
                # we'll need the "day" rep
                # or... both of them? e.g. max temp day + min temp night?
                weather_type = rep.get('W')
                wind_direction = rep.get('D')
                wind_speed = rep.get('S')
                visibility = rep.get('V')

    @task(run_every=timedelta(minutes=15))
    def import_forecasts(self, **metadata):
        content = urlopen(self.FORECASTS_URL % (self.location_id, settings.API_KEYS['metoffice']))\
            .read()
        forecasts = self.scrape_forecast_daily_xml(content)
