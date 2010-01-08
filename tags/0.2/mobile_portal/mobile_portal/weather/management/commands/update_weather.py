from django.core.management.base import NoArgsCommand

from xml.etree import ElementTree as ET
from datetime import datetime, tzinfo, timedelta
import urllib, re, email, sys
from django.contrib.gis.geos import Point
from mobile_portal.weather.models import (
    Weather, OUTLOOK_CHOICES, VISIBILITY_CHOICES, PRESSURE_STATE_CHOICES,
    SCALE_CHOICES
)

def rfc_2822_datetime(value):
    time_tz = email.utils.parsedate_tz(value)
    
    class tz(tzinfo):
        def utcoffset(self, dt):
            return timedelta(seconds=time_tz[9])
        def dst(self, dt):
            return timedelta(0)
        def __repr__(self):
            return "%02d%02d" % (time_tz[9]//3600, (time_tz[9]//60) % 60)

    return datetime(*(time_tz[:6] + (0, tz())))

class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list
    help = "Loads weather data"

    requires_model_validation = True

    OBSERVATIONS_URL = 'http://newsrss.bbc.co.uk/weather/forecast/%d/ObservationsRSS.xml'
    OBSERVATIONS_RE = re.compile(
        r'Temperature: (?P<temperature>-?\d+|N\/A).+Wind Direction: '
      + r'(?P<wind_direction>[NESW]{0,2}|N\/A), Wind Speed: (?P<wind_speed>\d+|N\/A).+Re'
      + r'lative Humidity: (?P<humidity>\d+|N\/A).+Pressure: (?P<pressure>\d+|N\/A).+'
      + r' (?P<pressure_state>rising|falling|steady|no change|N\/A), Visibility: (?P<visibility>[A-Za-z\/ ]+)')
    
    OBSERVATIONS_TITLE_RE = re.compile(
        r'(?P<day>[A-Za-z]+) at (?P<time>\d\d:\d\d).+\n(?P<outlook>[A-Za-z\/ ]+)\.'
    )
    
    FORECAST_URL = 'http://newsrss.bbc.co.uk/weather/forecast/%d/Next3DaysRSS.xml'
    FORECAST_RE = FE = (
        r'Max Temp: (?P<max_temperature>-?\d+|N\/A).+Min Temp: (?P<min_temperature>-?\d+|N\/A)'
      + r'.+Wind Direction: (?P<wind_direction>[NESW]{0,3}|N\/A), Wind Speed: '
      + r'(?P<wind_speed>\d+|N\/A).+Visibility: (?P<visibility>[A-Za-z\/ ]+), '
      + r'Pressure: (?P<pressure>\d+|N\/A).+Humidity: (?P<humidity>\d+|N\/A).+'
      + r'UV risk: (?P<uv_risk>[A-Za-z]+|N\/A), Pollution: (?P<pollution>[A-Za-z]+|N\/A), '
      + r'Sunrise: (?P<sunrise>\d\d:\d\d)[A-Z]{3}, Sunset: (?P<sunset>\d\d:\d\d)[A-Z]{3}'
    )
    FORECAST_RE = re.compile(FE)
    
    FORECAST_TITLE_RE = re.compile(
        r'(?P<day>[A-Za-z]+): (?P<outlook>[A-Za-z\/ ]+),'
    )
    
    CHANNEL_TITLE_RE = re.compile(
        r'BBC - Weather Centre - (Latest Observations|Forecast) for (?P<name>.+)'
    )
    
    OXFORD_BBC_ID = 25
    
    @staticmethod
    def get_observations_data(bbc_id):
        xml = ET.parse(urllib.urlopen(Command.OBSERVATIONS_URL % bbc_id))
        
        description = xml.find('.//item/description').text
        title = xml.find('.//item/title').text
        channel_title = xml.find('.//channel/title').text
    
        # Extract the data from the RSS item using regular expressions.
        data = Command.OBSERVATIONS_TITLE_RE.match(title).groupdict()
        data.update(Command.OBSERVATIONS_RE.match(description).groupdict())
        
        data.update(Command.CHANNEL_TITLE_RE.match(channel_title).groupdict())
        
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
        observed_date = rfc_2822_datetime(observed_date)
        # If the time is greater than the current time of day, it must have been at
        # least yesterday that this weather was observed
        if published_date[17:22] < data['time']:
            observed_date -= timedelta(1)
        # Keep going back in time until we find the right day
        while observed_date.strftime('%A') != data['day']:
            observed_date -= timedelta(1)
        published_date = rfc_2822_datetime(published_date)
            
        data['published_date'] = published_date
        data['observed_date'] = observed_date
        
        data['location'] = (
            float(xml.find('.//{http://www.w3.org/2003/01/geo/wgs84_pos#}lat').text),
            float(xml.find('.//{http://www.w3.org/2003/01/geo/wgs84_pos#}long').text),
        )
    
        return data
        
    @staticmethod
    def get_forecast_data(bbc_id):
        xml = ET.parse(urllib.urlopen(Command.FORECAST_URL % bbc_id))
        
        channel_title = xml.find('.//channel/title').text
        data = Command.CHANNEL_TITLE_RE.match(channel_title).groupdict()
        data['forecasts'] = {}
        data['modified_date'] = rfc_2822_datetime(xml.find('.//pubDate').text)
        
        for item in xml.findall('.//item'):
            desc = Command.FORECAST_RE.match(item.find('description').text).groupdict()
            title = Command.FORECAST_TITLE_RE.match(item.find('title').text).groupdict()
            
            published_date = item.find('pubDate').text
            dt = rfc_2822_datetime(published_date)
            while dt.strftime('%A') != title['day']:
                dt += timedelta(1)
                
            forecast = data['forecasts'][dt.date()] = {}
            forecast['observed_date'] = dt.date()
            
            forecast.update(desc)
            forecast.update(title)
            
            forecast['sunset'] = rfc_2822_datetime(
                published_date[:17] + forecast['sunset'] + ':00' + published_date[25:]
            ).time()
            forecast['sunrise'] = rfc_2822_datetime(
                published_date[:17] + forecast['sunrise'] + ':00' + published_date[25:]
            ).time()
        
            forecast['location'] = (
                float(xml.find('.//{http://www.w3.org/2003/01/geo/wgs84_pos#}lat').text),
                float(xml.find('.//{http://www.w3.org/2003/01/geo/wgs84_pos#}long').text),
            )
            
        return data
            
        
    @staticmethod
    def find_choice_match(choices, verbose):
        matches = [a for a,b in choices if (verbose or '').lower() == b]
        if len(matches) == 1:
            return matches[0]
        else:
            return None
            
    def handle_noargs(self, **options):
        observations = Command.get_observations_data(Command.OXFORD_BBC_ID)
        forecasts = Command.get_forecast_data(Command.OXFORD_BBC_ID)
        
        weathers = [(
            Weather.objects.get_or_create(bbc_id = Command.OXFORD_BBC_ID, ptype='o')[0], observations
        )]
        
        for k, v in forecasts['forecasts'].items():
            weathers.append( (
                Weather.objects.get_or_create(bbc_id = Command.OXFORD_BBC_ID, ptype='f', observed_date=k)[0],
                v
            ) )
            
        VERBATIM = (
            'temperature', 'wind_speed', 'humidity', 'pressure',
            'wind_direction', 'sunset', 'sunrise', 'observed_date',
            'published_date', 'name', 'min_temperature', 'max_temperature',
        )
        LOOKUP = (
            ('outlook', OUTLOOK_CHOICES),
            ('visibility', VISIBILITY_CHOICES),
            ('pressure_state', PRESSURE_STATE_CHOICES),
            ('uv_risk', SCALE_CHOICES),
            ('pollution', SCALE_CHOICES),
        )
        
        for weather, data in weathers:
            for k in VERBATIM:
                if k in data:
                    setattr(weather, k, data[k])
            
            for k, l in LOOKUP:
                if k in data:
                    setattr(weather, k, Command.find_choice_match(l, data[k]))
                
            weather.location = Point(data['location'], srid=4326)
        
        
            weather.save()
        
