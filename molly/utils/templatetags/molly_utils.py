try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

from lxml import etree
import math
from datetime import datetime
from dateutil.tz import tzutc, tzlocal

from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import SafeUnicode, mark_safe

from molly.utils.xslt import transform
from molly.wurfl import device_parents
from molly.apps.places import get_entity
from molly.apps.places.models import Entity
from molly.conf.applications import has_app_by_local_name

register = template.Library()

@register.filter
@stringfilter
def app_is_loaded(app):
    return has_app_by_local_name(app)

@register.filter
def sanitize_html(value, args=''):
    document = etree.fromstring(u'<body>%s</body>' % value, parser = etree.HTMLParser())

    args = args.split(',') + [None, None]
    id_prefix, class_prefix = args[0] or 'sani', args[1] or 'sani'

    document = transform(document, 'utils/sanitize_html.xslt', {
        'id_prefix': id_prefix,
        'class_prefix': class_prefix,
    })
    return SafeUnicode(etree.tostring(document)[6:-7])

@register.filter(name="gte")
def gte(value, arg):
    return value >= float(arg)

@register.filter(name="lte")
def lte(value, arg):
    return value <= arg

@register.filter(name="contains")
def contains(value, arg):
    return arg in value

@register.filter
def this_year(value, arg=None):
    if not arg:
        arg = datetime.now()
    return value.year == arg.year

@register.filter
def round_up_10(value):
    """
    Rounds a number up to the nearest 10
    """
    return '%d' % int(math.ceil(int(value)/10)*10)

UNUSUAL_NUMBERS = {
    '+448454647': '0845 46 47', # NHS Direct
    '+448457909090': '08457 90 90 90' # Samaritans
}

@register.filter(name="telephone")
def telephone(value, arg=None):
    """
    Formats UK telephone numbers to E.123 format (national notation)
    
    University number ranges are also formatted according to internal guidelines
    """
    
    # Normalise a number
    value = value.replace(" ", "").replace("-", "")
    if value.startswith("0"):
        value = "+44" + value[1:]
    normalised = value
    
    # Check if it's a number which is formatted in a special way
    if normalised in UNUSUAL_NUMBERS:
        value = UNUSUAL_NUMBERS[normalised]
    else:
        # Figure out how to format that number
        
        # Convert UK numbers into national format
        if value.startswith("+44"):
            value = "0" + value[3:]
        
        # Now apply rules on how to split up area codes
        if value[:8] in ('01332050', '01382006'):
            # Direct dial only
            value = value[:5] + " " + value[5:]
        elif value[:7] in ('0141005', '0117101') or value[:6] in ('011800',):
            # Direct dial only
            value = value[:4] + " " + value[4:7] + " " + value[7:]
        elif value[:7] in ('0200003',):
            # Direct dial only
            value = value[:3] + " " + value[3:7] + " " + value[7:]
        elif value.startswith('01'):
            if value[2] == '1' or value[3] == '1':
                # 4 digit area codes
                area_code = value[:4]
                local_part =  value[4:7] + " " + value[7:]
            elif value[:6] in (
                        '013873', # Langholm
                        '015242', # Hornby
                        '015394', # Hawkshead
                        '015395', # Grange-over-Sands
                        '015396', # Sedbergh
                        '016973', # Wigton
                        '016974', # Raughton Head
                        '016977', # Brampton
                        '017683', # Appleby
                        '017684', # Pooley Bridge
                        '017687', # Keswick
                        '019467', # Gosforth
                    ):
                # 6 digit area codes
                area_code = value[:4] + " " + value[4:6]
                local_part = value[6:]
            else:
                # 5 digit
                area_code = value[:5]
                local_part = value[5:]
            
            value = "(%s) %s" % (area_code, local_part)
        
        elif value.startswith('02'):
            # 3 digit area codes
            value = "(%s) %s %s" % (value[:3], value[3:7], value[7:])
        
        elif value.startswith('0500') or value.startswith('0800'):
            # direct dial - 4 digit prefix, short following
            value = "%s %s" % (value[:4], value[4:])
        
        elif value.startswith('03') or value.startswith('08') or value.startswith('09'):
            # direct dial - 4 digit prefix
            value = "%s %s %s" % (value[:4], value[4:7], value[7:])
        
        elif value.startswith('05') or value.startswith('070'):
            # direct dial - 3 digit prefix
            value = "%s %s %s" % (value[:3], value[3:7], value[7:])
        
        elif value.startswith('07'):
            # direct dial - 5 digit prefix, short following
            value = "%s %s" % (value[:5], value[5:])

    # Now apply University rules:
    if value[:10] in ('(01865) 27', '(01865) 28', '(01865) 43', '(01865) 61'):
            # Oxford - list of internal number prefixes here:
            # http://www.oucs.ox.ac.uk/telecom/directories/intdiraccess.xml
            value = "(01865 " + value[8] + ")" + value[9:]

    if arg == 'nolink':
        return value
    else:
        return mark_safe('<a href="tel:%s">%s</a>' % (normalised, value))

@register.filter
def telephone_uri(value):
    value = value.replace(" ", "").replace('-','')
    if value.startswith("0"):
        value = "+44" + value[1:]
    value = "tel:" + value

    return value

@register.filter(name="device_has_parent")
def device_has_parent(value, arg):
    if not value:
        return False
    return arg in device_parents[value.devid]

@register.filter
def header_width(value):
    try:
        value = int(value)
        if value < 160:
            return 128
        elif value < 240:
            return 160
    except ValueError, e:
        pass
    return 128

@register.filter('get_entity')
def get_entity_filter(value):
    return get_entity(*value)

@register.filter
def localize_utc(value):
    """
    Localise a UTC datetime
    """
    if isinstance(value, datetime):
        return value.replace(tzinfo=tzutc()).astimezone(tzlocal())
    else:
        return value