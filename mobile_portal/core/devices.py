RESOLUTIONS = {
    'BlackBerry/9000': (480, 320),
    'Nokia/E61': (320, 240),
    'iPhone/3GS': (480, 320),
    'iPhone/3G': (480, 320),
}

UA_REGEXES = (
    (r'Opera Mini/(?P<version>[\d\.]+)', 'OperaMini/%(version)s'),
    (r'BlackBerry(?P<model>\d{4})/(?P<version>[\d\.]+)', 'BlackBerry/%(version)s'),
    (r'Firefox/(?P<version>[\d\.]+((a|b|rc)\d+)?)', 'Firefox/%(version)s'),
)

class Device(object):
    name = None
    resolution = None
    gps = None
    wifi = None
    qwerty = None

class Nokia(Device):
    pass

class Nokia_ESeries(Nokia):
    resolution = (320, 240)

class Nokia_E61(Nokia_ESeries):
    name = "Nokia E61"

def resolve_device(request):
