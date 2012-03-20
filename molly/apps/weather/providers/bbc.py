from datetime import datetime, tzinfo, timedelta
import email
import logging
import random
import re
import socket
import traceback
import urllib
from xml.etree import ElementTree as ET

from dateutil.tz import tzoffset
from django.contrib.gis.geos import Point
from django.utils.translation import ugettext_lazy as _

from molly.conf.provider import Provider, task
from molly.apps.weather.models import (
    Weather, OUTLOOK_CHOICES, VISIBILITY_CHOICES, PRESSURE_STATE_CHOICES,
    SCALE_CHOICES, PTYPE_OBSERVATION, PTYPE_FORECAST
)

logger = logging.getLogger(__name__)

class BBCWeatherProvider(Provider):
    """
    Scrapes BBC RSS feeds to obtain weather information
    """

    ATTRIBUTION = {
        'title': _('BBC Weather'),
        'url': _('http://bbc.co.uk/weather/')
    }

    FRESHNESS = timedelta(hours=3)

    def __init__(self, location_id):
        self.location_id = location_id
        self.id = 'bbc/%d' % location_id

    def fetch_observation(self):
        return Weather.objects.get(location_id=self.id,
                                   ptype=PTYPE_OBSERVATION)

    def fetch_forecasts(self):
        return Weather.objects.filter(
                location_id=self.id, ptype=PTYPE_FORECAST,
                observed_date__gte=datetime.now().date()
            ).order_by('observed_date')

    @staticmethod
    def _rfc_2822_datetime(value):
        time_tz = email.utils.parsedate_tz(value)
        tz = tzoffset(time_tz[9], time_tz[9])

        return datetime(*(time_tz[:6] + (0, tz)))

    @staticmethod
    def _find_choice_match(choices, verbose):
        matches = [a for a,b in choices if (verbose or '').lower() == b]
        if len(matches) == 1:
            return matches[0]
        else:
            return None

    _OBSERVATIONS_URL = \
        'http://newsrss.bbc.co.uk/weather/forecast/%d/ObservationsRSS.xml'
    _OBSERVATIONS_RE = re.compile(
          r'Temperature: (?P<temperature>-?\d+|N\/A).+'
        + r'Wind Direction: '
        + r'(?P<wind_direction>[NESW]{0,2}|N\/A)'
        + r', Wind Speed: (?P<wind_speed>\d+|N\/A).+'
        + r'Relative Humidity: (?P<humidity>\d+|N\/A).+'
        + r'Pressure: (?P<pressure>\d+|N\/A).+'
        + r' (?P<pressure_state>rising|falling|steady|no change|N\/A), '
        + r'Visibility: (?P<visibility>[A-Za-z\/ ]+)')

    _OBSERVATIONS_TITLE_RE = re.compile(
        r'(?P<day>[A-Za-z]+) at (?P<time>\d\d:\d\d).+' +
        r'\n(?P<outlook>[A-Za-z\/ ]+)\.'
    )

    _FORECAST_URL = \
        'http://newsrss.bbc.co.uk/weather/forecast/%d/Next3DaysRSS.xml'
    _FORECAST_RE = re.compile(
        r'Max Temp:\s*(?P<max_temperature>-?\d+|N\/A).+'
        + r'Min Temp:\s*(?P<min_temperature>-?\d+|N\/A)'
        + r'.+Wind Direction:\s*(?P<wind_direction>[NESW]{0,3}|N\/A),\s*'
        + r'Wind Speed:\s*(?P<wind_speed>\d+|N\/A).+'
        + r'Visibility:\s*(?P<visibility>[A-Za-z\/ ]+),\s*'
        + r'Pressure:\s*(?P<pressure>\d+|N\/A).+'
        + r'Humidity:\s*(?P<humidity>\d+|N\/A).+'
        + r'(UV risk:\s*(?P<uv_risk>[A-Za-z]+|N\/A),)?\s*'
        + r'Pollution:\s*(?P<pollution>[A-Za-z]+|N\/A),\s*'
        + r'Sunrise:\s*(?P<sunrise>\d\d:\d\d).+,\s*'
        + r'Sunset:\s*(?P<sunset>\d\d:\d\d).+'
    )

    _FORECAST_TITLE_RE = re.compile(
        r'(?P<day>[A-Za-z]+): (?P<outlook>[A-Za-z\/ ]+),'
    )

    _CHANNEL_TITLE_RE = re.compile(
        r'BBC - Weather Centre - '
        + r'(Latest Observations|Forecast) for (?P<name>.+)'
    )

    @task(run_every=timedelta(minutes=15))
    def import_data(self, **metadata):
        """
        Pulls weather data from the BBC
        """
        socket.setdefaulttimeout(5)
        try:
            observations = self.get_observations_data()
            forecasts = self.get_forecast_data()
        except Exception as e:
            logger.exception("Error importing weather data from BBC")
            return metadata

        # We only keep the most recent observation. This avoids the DB growing
        # without limit. We also may not have a right to store this data.
        weathers = [(
            Weather.objects.get_or_create(
                location_id=self.id, ptype=PTYPE_OBSERVATION)[0],
            observations
        )]

        for observation_date, forecast in forecasts['forecasts'].items():
            weathers.append( (
                Weather.objects.get_or_create(
                    location_id=self.id, ptype=PTYPE_FORECAST,
                    observed_date=observation_date)[0],
                forecast
            ) )

        VERBATIM = [
            'temperature', 'wind_speed', 'humidity', 'pressure',
            'wind_direction', 'sunset', 'sunrise', 'observed_date',
            'published_date', 'name', 'min_temperature', 'max_temperature',
        ]
        LOOKUP = [
            ('outlook', OUTLOOK_CHOICES),
            ('visibility', VISIBILITY_CHOICES),
            ('pressure_state', PRESSURE_STATE_CHOICES),
            ('uv_risk', SCALE_CHOICES),
            ('pollution', SCALE_CHOICES),
        ]

        for weather, data in weathers:
            for feature in VERBATIM:
                if feature in data:
                    setattr(weather, feature, data[feature])

            for feature, values in LOOKUP:
                if feature in data:
                    setattr(weather, feature,
                            self._find_choice_match(values, data[feature]))

            weather.location = Point(data['location'], srid=4326)
            weather.save()

        return metadata

    def get_observations_data(self):
        xml = ET.parse(urllib.urlopen(
            self._OBSERVATIONS_URL % self.location_id))

        description = xml.find('.//item/description').text
        title = xml.find('.//item/title').text
        channel_title = xml.find('.//channel/title').text

        # Extract the data from the RSS item using regular expressions.
        data = self._OBSERVATIONS_TITLE_RE.match(title).groupdict()
        data.update(self._OBSERVATIONS_RE.match(description).groupdict())

        data.update(self._CHANNEL_TITLE_RE.match(channel_title).groupdict())

        # Normalise integer fields with None for unknown values
        for k in ['temperature','wind_speed','humidity','pressure']:
            try:
                data[k] = int(data[k])
            except ValueError:
                data[k] = None
        for k in data:
            if data[k] in ['','N/A']:
                data[k] = None

        # Calculate datetimes for observed and published dates
        published_date = xml.find('.//item/pubDate').text
        observed_date = published_date
        observed_date = observed_date[:17] + data['time'] + observed_date[22:]
        observed_date = self._rfc_2822_datetime(observed_date)
        # If the time is greater than the current time of day, it must have been
        # at least yesterday that this weather was observed
        if published_date[17:22] < data['time']:
            observed_date -= timedelta(1)
        # Keep going back in time until we find the right day
        while observed_date.strftime('%A') != data['day']:
            observed_date -= timedelta(1)
        published_date = self._rfc_2822_datetime(published_date)

        data['published_date'] = published_date
        data['observed_date'] = observed_date

        data['location'] = (
            float(xml.find(
                './/{http://www.w3.org/2003/01/geo/wgs84_pos#}lat').text),
            float(xml.find(
                './/{http://www.w3.org/2003/01/geo/wgs84_pos#}long').text),
        )

        return data

    def get_forecast_data(self):
        xml = ET.parse(urllib.urlopen(self._FORECAST_URL % self.location_id))

        channel_title = xml.find('.//channel/title').text
        data = self._CHANNEL_TITLE_RE.match(channel_title).groupdict()
        data['forecasts'] = {}
        data['modified_date'] = self._rfc_2822_datetime(
            xml.find('.//pubDate').text)

        for item in xml.findall('.//item'):
            desc = self._FORECAST_RE.match(
                item.find('description').text).groupdict()
            title = self._FORECAST_TITLE_RE.match(
                item.find('title').text).groupdict()

            published_date = item.find('pubDate').text
            dt = self._rfc_2822_datetime(published_date)
            while dt.strftime('%A') != title['day']:
                dt += timedelta(1)

            forecast = data['forecasts'][dt.date()] = {}
            forecast['observed_date'] = dt.date()

            forecast.update(desc)
            forecast.update(title)

            forecast['sunset'] = self._rfc_2822_datetime(
                published_date[:17] + forecast['sunset']
                + ':00' + published_date[25:]
            ).time()
            forecast['sunrise'] = self._rfc_2822_datetime(
                published_date[:17] + forecast['sunrise']
                + ':00' + published_date[25:]
            ).time()

            forecast['location'] = (
                float(xml.find(
                    './/{http://www.w3.org/2003/01/geo/wgs84_pos#}lat').text),
                float(xml.find(
                    './/{http://www.w3.org/2003/01/geo/wgs84_pos#}long').text),
            )

        return data
