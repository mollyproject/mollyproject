import logging
from urllib2 import urlopen
from lxml import etree
from datetime import datetime, timedelta

from django.utils.translation import ugettext_lazy as _

from molly.conf.providers import Provider, task
from molly.apps.weather.models import Weather

logger = logging.getLogger(__name__)


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
