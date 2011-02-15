try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

from lxml import etree

from datetime import datetime

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

UNUSUAL_NUMBERS = {
    '+448454647': '0845 46 47',
    '+448457909090': '08457 90 90 90'
}

@register.filter(name="telephone")
def telephone(value, arg):
    value = value.replace(" ", "").replace("-", "")
    if value.startswith("0"):
        value = "+44" + value[1:]

    normalised = value

    if normalised in UNUSUAL_NUMBERS:
        value = UNUSUAL_NUMBERS[normalised]
    else:
        if value.startswith("+44"):
            value = "0" + value[3:]

        for dialing_code in ['01865', '0845']:
            if value.startswith(dialing_code):
                value = dialing_code + " " + value[len(dialing_code):]

        if value.startswith('01865 2'):
            value = "01865 (2)" + value[7:]

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