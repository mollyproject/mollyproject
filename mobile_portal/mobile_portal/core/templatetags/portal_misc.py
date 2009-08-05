import simplejson, urllib, urllib2
from django import template

from mobile_portal.core.utils import AnyMethodRequest
from mobile_portal.core.models import ExternalImage, ExternalImageSized

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
    
@register.tag(name='external_image')
def external_image(parser, token):
    args = token.split_contents()
    if len(args) != 2:
        raise template.TemplateSyntaxError, "%r takes one argument (the image location)" % token.contents.split()[0]
    else:
        return ExternalImageNode(template.Variable(args[1]))

class ExternalImageNode(template.Node):
    def __init__(self, url):
        self.url = url
        
    def render(self, context):
        url, width = self.url.resolve(context), context['device'].max_image_width

        ei, created = ExternalImage.objects.get_or_create(url=url)
        
        request = AnyMethodRequest(url, method='HEAD')
        response = urllib2.urlopen(request)
        
        print "Woo!"
        print dir(response)
        if response.headers['ETag'] != ei.etag:
            print "Boo"
            ExternalImageSized.objects.filter(external_image=ei).delete()
            ei.etag = response.headers['Etag']
            ei.save()
        
        print "Whee"
        
        eis, created = ExternalImageSized.objects.get_or_create(external_image=ei, width=width)
                
        print "Here"
        print eis.get_absolute_url()
        return eis.get_absolute_url()