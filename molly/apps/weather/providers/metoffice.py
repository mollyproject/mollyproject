import logging
from urllib2 import urlopen
from lxml import etree
from datetime import datetime, timedelta

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

class MetOfficeProvider(Provider):
    """
    Scrapes MetOffice DataPoint / observations API
    TODO: this class should be splitted in two (observations and forecasts).
    """

    ATTRIBUTION = {
        'title': _('MetOffice'),
        'url': _('http://www.metoffice.gov.uk/')
    }

    FRESHNESS = timedelta(hours=3)

    def __init__(self, location_id):
        self.location_id = location_id
        self.id = 'metoffice/%d' % location_id

    def fetch_observation(self):
        return Weather.objects.all()

    def scrape_xml(self, content):
        """
        Scrape the XML content representing a site,
        returns a dict containing the first observation
        (most recent).
        """
        xml = etree.fromstring(content)
        period = xml.findall('//Period')[0]
        last_observation = xml.findall('//Rep')[0]
        observations = {
            'datetime': datetime(2011, 11, 22, 20, 00),
            'weather_type': 104,
            'visibility': 'MO',
        }
        return observations
