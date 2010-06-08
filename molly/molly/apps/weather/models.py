from datetime import datetime, time
from django.contrib.gis.db import models

PTYPE_CHOICES = (
    ('o', 'observation'),
    ('f', 'forecast'),
)

PRESSURE_STATE_CHOICES = (
    ('+', 'rising'),
    ('-', 'falling'),
    ('~', 'steady'),
    ('c', 'no change'),
)

VISIBILITY_CHOICES = (
    ('vp', 'very poor visibility'),
    ('p',  'poor visibility '),
    ('vg', 'very good visibility'),
    ('g', 'good visibility'),
    ('df', 'dense fog'),
    ('f', 'fog'),
    ('e', 'excellent visibility'),
    ('m', 'moderate visibility'),
)

OUTLOOK_CHOICES = (
    ('si', 'sunny intervals'),
    ('gc', 'grey cloud'),
    ('hr', 'heavy rain'),
    ('s', 'sunny'),
    ('lr', 'light rain'),
    ('pc', 'partly cloudy'),
    ('f', 'fog'),
    ('wc', 'white cloud'),
    ('tst', 'thunder storm'),
    ('m', 'mist'),
    ('tsh', 'thundery shower'),
    ('lrs', 'light rain shower'),
    ('cs', 'clear sky'),
    ('d', 'drizzle'),
    ('h', 'hail'),
    ('lsn', 'light snow'),
    ('sn', 'snow'),
    ('hsn', 'heavy snow'),
    ('unk', 'n/a'),
)

OUTLOOK_TO_ICON = {
    'si':  'cloudy2',
    'gc':  'overcast',
    'hr':  'shower3',
    's':   'sunny',
    'lr':  'light_rain',
    'pc':  'cloudy3%(night)s',
    'f':   'fog%(night)s',
    'wc':  'cloudy5',
    'tst': 'tstorm1',
    'm':   'mist%(night)s',
    'tsh': 'tstorm3',
    'lrs': 'shower2%(night)s',
    'cs':  'sunny%(night)s',
    'd':   'shower1%(night)s',
    'h':   'hail',
    'lsn': 'snow1%(night)s',
    'sn':  'snow3%(night)s',
    'hsn': 'snow5',
    'unk': 'dunno',
}

SCALE_CHOICES = (
    ('l', 'low'),
    ('m', 'medium'),
    ('h', 'high'),
)

class Weather(models.Model):
    location_id = models.CharField(max_length=16)

    ptype = models.CharField(max_length=1, choices=PTYPE_CHOICES)

    name = models.TextField(null=True)

    outlook = models.CharField(null=True, max_length=3, choices=OUTLOOK_CHOICES)

    published_date = models.DateTimeField(null=True)
    observed_date = models.DateTimeField(null=True)
    modified_date = models.DateTimeField(auto_now=True)

    temperature = models.IntegerField(null=True)
    wind_direction = models.CharField(null=True, max_length=3)
    wind_speed = models.IntegerField(null=True)
    humidity = models.IntegerField(null=True)
    pressure = models.PositiveIntegerField(null=True)
    pressure_state = models.CharField(null=True, max_length=1, choices=PRESSURE_STATE_CHOICES)
    visibility = models.CharField(null=True, max_length=2, choices=VISIBILITY_CHOICES)

    location = models.PointField(srid=4326, null=True)

    min_temperature = models.IntegerField(null=True)
    max_temperature = models.IntegerField(null=True)
    uv_risk = models.CharField(max_length=1, choices=SCALE_CHOICES, null=True)
    pollution = models.CharField(max_length=1, choices=SCALE_CHOICES, null=True)
    sunset = models.TimeField(null=True)
    sunrise = models.TimeField(null=True)

    def icon(self):
        now = datetime.now().time()
        if now > time(7) or now > time(21):
            night = '_night'
        else:
            night = ''
        return OUTLOOK_TO_ICON.get(self.outlook, 'dunno') % {'night':night}

