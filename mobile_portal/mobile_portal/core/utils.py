from __future__ import division
from xml.etree import ElementTree as ET
import re, email.utils
from datetime import datetime, timedelta, tzinfo, time

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


try:
    from models import Feed
    def get_data(url):
        return Feed.fetch(url, category='weather', fetch_period=600, return_data=True, raise_if_error=True)
except ImportError:
    import urllib
    def get_data(url):
        response = urllib.urlopen(url)
        if response.code == 200:
            return urllib.urlopen(url).read()
        else:
            raise IOError

WEATHER_URL = 'http://newsrss.bbc.co.uk/weather/forecast/%d/ObservationsRSS.xml'
WEATHER_RE = re.compile(
    r'Temperature: (?P<temperature>-?\d+|N\/A).+Wind Direction: '
  + r'(?P<wind_direction>[NESW]{0,2}|N\/A), Wind Speed: (?P<wind_speed>\d+|N\/A).+Re'
  + r'lative Humidity: (?P<humidity>\d+|N\/A).+Pressure: (?P<pressure>\d+|N\/A).+'
  + r' (?P<pressure_state>rising|falling|steady|no change|N\/A), Visibility: (?P<visibility>[A-Za-z\/ ]+)')

WEATHER_TITLE_RE = re.compile(
    r'(?P<day>[A-Za-z]+) at (?P<time>\d\d:\d\d).+\n(?P<outlook>[A-Za-z\/ ]+)\.'
)

def latest_weather(location=25):
    xml = get_data(WEATHER_URL % location)
    xml = ET.fromstring(xml)
    
    description = xml.find('.//item/description').text
    title = xml.find('.//item/title').text

    # Extract the data from the RSS item using regular expressions.
    data = WEATHER_TITLE_RE.match(title).groupdict()
    data.update(WEATHER_RE.match(description).groupdict())
    
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

    return data

OUTLOOK_TO_ICON = {
    'grey cloud':        'overcast',
    'sunny':             'sunny',
    'sunny intervals':   'cloudy2',
    'light rain':        'light_rain',
    'heavy rain':        'shower3',
    'partly cloudy':     'cloudy3%(night)s',
    'clear sky':         'sunny%(night)s',
    'white cloud':       'cloudy5',
    'mist':              'mist%(night)s',
    'thundery shower':   'tstorm3',
    'drizzle':           'shower1%(night)s',
    'light rain shower': 'shower2%(night)s',
    'fog':               'fog%(night)s',
    'hail':              'hail',
    'light snow':        'snow1%(night)s',
    'snow':              'snow3%(night)s',
    'heavy snow':        'snow5',
}    

def outlook_to_icon(outlook):
    now = datetime.now().time()
    if now > time(7) or now > time(21):
        night = '_night'
    else:
        night = '' 
    return OUTLOOK_TO_ICON.get(outlook, 'dunno') % {'night':night}

if __name__ == '__main__':
    print latest_weather()
    print outlook_to_icon(latest_weather()['outlook'])