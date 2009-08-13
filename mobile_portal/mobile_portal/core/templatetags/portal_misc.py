import simplejson, urllib, urllib2
from django import template
from django.utils.safestring import mark_safe

from mobile_portal.core.utils import AnyMethodRequest
from mobile_portal.core.models import ExternalImage, ExternalImageSized
from mobile_portal.oxpoints.models import Entity

register = template.Library()

@register.filter(name="gte")
def gte(value, arg):
    return value >= float(arg)
    
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
    if len(args) != 2:
        raise template.TemplateSyntaxError, "%r takes one argument (the image location)" % token.contents.split()[0]
    else:
        return ExternalImageNode(template.Variable(args[1]))

class ExternalImageNode(template.Node):
    """
    Takes the form {% external_image url %} and renders as a URL pointing at
    the given image resized to match the device's max_image_width.
    """
    
    def __init__(self, url):
        self.url = url
        
    def render(self, context):
        url, width = self.url.resolve(context), context['device'].max_image_width

        ei, created = ExternalImage.objects.get_or_create(url=url)
        
        request = AnyMethodRequest(url, method='HEAD')
        response = urllib2.urlopen(request)

        # Check whether the image has changed since last we looked at it        
        if response.headers.get('ETag', ei.etag) != ei.etag or response.headers.get('Last-Modified') != ei.last_modified:

            # Can't use the shorter EIS.objects.filter(...).delete() as that
            # doesn't call the delete() method on individual objects, resulting
            # in the old images not being deleted.
            for eis in ExternalImageSized.objects.filter(external_image=ei):
                eis.delete()
            ei.etag = response.headers.get('Etag')
            ei.last_modified = response.headers.get('Last-Modified')
            ei.save()
        
        eis, created = ExternalImageSized.objects.get_or_create(external_image=ei, width=width)

        return eis.get_absolute_url()
        
UNUSUAL_NUMBERS = {
    '+448454647': '0845 46 47',
    '+448457909090': '08457 90 90 90'
}

@register.filter(name="telephone")
def telephone(value):
    value = value.replace(" ", "")
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
            
    return mark_safe('<a href="tel:%s">%s</a>' % (normalised, value))
    