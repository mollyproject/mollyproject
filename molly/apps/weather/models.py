from datetime import datetime, time

from django.contrib.gis.db import models
from django.utils.translation import ugettext_lazy as _

PTYPE_OBSERVATION = 'o'
PTYPE_FORECAST = 'f'
PTYPE_CHOICES = (
    (PTYPE_OBSERVATION, _('observation')),
    (PTYPE_FORECAST, _('forecast')),
)

PRESSURE_STATE_CHOICES = (
    # Translators: Weather pressure states
    ('+', _('rising')),
    ('-', _('falling')),
    ('~', _('steady')),
    ('c', _('no change')),
)

VISIBILITY_CHOICES = (
    ('vp', _('very poor visibility')),
    ('p',  _('poor visibility ')),
    ('vg', _('very good visibility')),
    ('g', _('good visibility')),
    ('df', _('dense fog')),
    ('f', _('fog')),
    ('e', _('excellent visibility')),
    ('m', _('moderate visibility')),
)

OUTLOOK_CHOICES = (
    ('si', _('sunny intervals')),
    ('gc', _('grey cloud')),
    ('hr', _('heavy rain')),
    ('s', _('sunny')),
    ('lr', _('light rain')),
    ('pc', _('partly cloudy')),
    ('f', _('fog')),
    ('wc', _('white cloud')),
    ('tst', _('thunder storm')),
    ('m', _('mist')),
    ('tsh', _('thundery shower')),
    ('lrs', _('light rain shower')),
    ('cs', _('clear sky')),
    ('d', _('drizzle')),
    ('h', _('hail')),
    ('lsn', _('light snow')),
    ('sn', _('snow')),
    ('hsn', _('heavy snow')),
    ('unk', _('n/a')),
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
    ('l', _('low')),
    ('m', _('medium')),
    ('h', _('high')),
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
    pressure_state = models.CharField(null=True, max_length=1,
                                      choices=PRESSURE_STATE_CHOICES)
    visibility = models.CharField(null=True, max_length=2,
                                  choices=VISIBILITY_CHOICES)

    location = models.PointField(srid=4326, null=True)

    min_temperature = models.IntegerField(null=True)
    max_temperature = models.IntegerField(null=True)
    uv_risk = models.CharField(max_length=1, choices=SCALE_CHOICES, null=True)
    pollution = models.CharField(max_length=1, choices=SCALE_CHOICES, null=True)
    sunset = models.TimeField(null=True)
    sunrise = models.TimeField(null=True)
    
    @property
    def icon(self):
        now = datetime.now().time()
        if now < time(7) or now > time(21):
            night = '_night'
        else:
            night = ''
        return OUTLOOK_TO_ICON.get(self.outlook, 'dunno') % {'night':night}

