import simplejson, urllib, urllib2
from datetime import datetime
from django import template
from django.utils.safestring import mark_safe

from molly.core.utils import AnyMethodRequest, resize_external_image
from molly.core.models import ExternalImage, ExternalImageSized
from molly.maps.models import Entity
from molly.wurfl import device_parents
from molly.maps.utils import get_entity
from molly.utils.ox_dates import format_today, ox_date_dict

register = template.Library()

@register.filter(name="gte")
def gte(value, arg):
    return value >= float(arg)
    
@register.filter(name="lte")
def lte(value, arg):
    return value <= arg

@register.filter(name="contains")
def gte(value, arg):
    return arg in value

@register.filter
def this_year(value, arg=None):
    if not arg:
        arg = datetime.now()
    return value.year == arg.year
    
@register.filter(name="oxp_id")
def oxp_id(value):
    prefix = 'http://m.ox.ac.uk/oxpoints/id/'
    try:
        if value['uri'].startswith(prefix):
            return value['uri'][len(prefix):]
        else:
            return ""
    except:
        return ""

@register.filter(name="load_oxp_json")
def load_oxp_json(value):
    return simplejson.load(urllib.urlopen(value['uri']+'.json'))[0]
    
@register.filter(name="oxp_portal_url")
def oxp_portal_url(value):
    try:
        return Entity.objects.get(oxpoints_id=int(oxp_id(value))).get_absolute_url()
    except Entity.DoesNotExist:
        return ""
    
@register.tag(name='external_image')
def external_image(parser, token):
    args = token.split_contents()
    if not len(args) in (2, 3):
        raise template.TemplateSyntaxError, "%r takes one argument (the image location)" % token.contents.split()[0]
    if len(args) == 3:
        return ExternalImageNode(template.Variable(args[1]), False)
    else:
        return ExternalImageNode(template.Variable(args[1]))

class ExternalImageNode(template.Node):
    """
    Takes the form {% external_image url %} and renders as a URL pointing at
    the given image resized to match the device's max_image_width.
    """

    def __init__(self, url, just_url=True):
        self.url, self.just_url = url, just_url

    def render(self, context):
        url, width = self.url.resolve(context), context['device'].max_image_width

        eis = resize_external_image(url, width)

        if not eis:
            return ''
        elif self.just_url:
            return eis.get_absolute_url()
        else:
            return """<div class="backgrounded-image" style="background-image:url('%s'); height:%dpx"> </div>""" % (eis.get_absolute_url(), eis.height)

        
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
    value = int(value)
    if value < 160:
        return 128
    elif value < 240:
        return 160
    else:
        return 240

@register.filter('get_entity')
def get_entity_filter(value):
    return get_entity(*value)
    
@register.simple_tag
def oxford_date_today():
    return format_today()
    
@register.filter('oxdate')
def oxdate(value, arg):
    return arg % ox_date_dict(value)
