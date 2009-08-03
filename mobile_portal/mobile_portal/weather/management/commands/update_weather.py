from django.core.management.base import NoArgsCommand

from xml.etree import ElementTree as ET
from datetime import datetime, tzinfo, timedelta
import urllib, re, email
from django.contrib.gis.geos import Point
from mobile_portal.weather.models import Weather, OUTLOOK_CHOICES, VISIBILITY_CHOICES, PRESSURE_STATE_CHOICES

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

    WEATHER_URL = 'http://newsrss.bbc.co.uk/weather/forecast/%d/ObservationsRSS.xml'
    WEATHER_RE = re.compile(
        r'Temperature: (?P<temperature>-?\d+|N\/A).+Wind Direction: '
      + r'(?P<wind_direction>[NESW]{0,2}|N\/A), Wind Speed: (?P<wind_speed>\d+|N\/A).+Re'
      + r'lative Humidity: (?P<humidity>\d+|N\/A).+Pressure: (?P<pressure>\d+|N\/A).+'
      + r' (?P<pressure_state>rising|falling|steady|no change|N\/A), Visibility: (?P<visibility>[A-Za-z\/ ]+)')
    
    WEATHER_TITLE_RE = re.compile(
        r'(?P<day>[A-Za-z]+) at (?P<time>\d\d:\d\d).+\n(?P<outlook>[A-Za-z\/ ]+)\.'
    )
    
    WEATHER_CHANNEL_TITLE_RE = re.compile(
        r'BBC - Weather Centre - Latest Observations for (?P<name>.+)'
    )
    
    OXFORD_BBC_ID = 25
    
    @staticmethod
    def get_weather_data(bbc_id):
        xml = ET.parse(urllib.urlopen(Command.WEATHER_URL % bbc_id))
        
        description = xml.find('.//item/description').text
        title = xml.find('.//item/title').text
        channel_title = xml.find('.//channel/title').text
    
        # Extract the data from the RSS item using regular expressions.
        data = Command.WEATHER_TITLE_RE.match(title).groupdict()
        data.update(Command.WEATHER_RE.match(description).groupdict())
        
        print channel_title, Command.WEATHER_TITLE_RE
        data.update(Command.WEATHER_CHANNEL_TITLE_RE.match(channel_title).groupdict())
        
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
            
        data['published'] = published_date
        data['observed'] = observed_date
        
        data['location'] = (
            float(xml.find('.//{http://www.w3.org/2003/01/geo/wgs84_pos#}lat').text),
            float(xml.find('.//{http://www.w3.org/2003/01/geo/wgs84_pos#}long').text),
        )
    
        return data
        
    @staticmethod
    def find_choice_match(choices, verbose):
        matches = [a for a,b in choices if verbose.lower() == b]
        print matches
        if len(matches) == 1:
            return matches[0]
        else:
            return None
            
    def handle_noargs(self, **options):
        data = Command.get_weather_data(Command.OXFORD_BBC_ID)
        
        weather, created = Weather.objects.get_or_create(bbc_id = Command.OXFORD_BBC_ID)
        
        weather.temperature = data['temperature']
        weather.wind_speed = data['wind_speed']
        weather.humidity = data['humidity']
        weather.pressure = data['pressure']
        weather.wind_direction = data['wind_direction']
        
        weather.outlook = Command.find_choice_match(OUTLOOK_CHOICES, data['outlook'])
        weather.visibility = Command.find_choice_match(VISIBILITY_CHOICES, data['visibility'])
        weather.pressure_state = Command.find_choice_match(PRESSURE_STATE_CHOICES, data['pressure_state'])
        
        weather.published_date = data['published']
        weather.observed_date = data['observed']
        
        weather.name = data['name']
        weather.location = Point(data['location'], srid=4326)
        
        print weather.pressure_state
        print weather.get_pressure_state_display()
        weather.save()