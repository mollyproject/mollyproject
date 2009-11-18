from datetime import datetime
import oauth.oauth as oauth
import urllib, urllib2, base64, pytz, simplejson
from xml.etree import ElementTree as ET
import xml.utils.iso8601

from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from django.conf import settings


from mobile_portal.core.renderers import mobile_render
from mobile_portal.core.handlers import BaseView
from oauth_tools import SakaiOAuthClient
from mobile_portal.secure.views import OAuthView

def parse_iso_8601(s):
    return datetime.fromtimestamp(xml.utils.iso8601.parse(s)).replace(tzinfo=pytz.utc)

class IndexView(BaseView):
    def handle_GET(self, request, context):
        return mobile_render(request, context, 'sakai/index')

class SakaiView(OAuthView):
    consumer_secret = settings.SAKAI_CONSUMER_SECRET
    access_token_name = 'sakai_access_token'
    client = SakaiOAuthClient
    signature_method = oauth.OAuthSignatureMethod_PLAINTEXT()
    
class SakaiView(BaseView):
    def __call__(self, request, *args, **kwargs):
        
        opener = urllib2.build_opener()
        opener.addheaders = [
            ('Authorization', 'Basic %s' % base64.b64encode('admin:Cie9shoo')),
            ('Cookie', 'JSESSIONID=fb00b3b3-3177-4149-a4c7-7ed37764676d.localhost'),
            ('User-Agent', 'm.ox.ac.uk/0.2'),
        ]
        
        return super(SakaiView, self).__call__(request, opener, *args, **kwargs)
    
    def build_url(self, url):
        return '%s%s' % (settings.SAKAI_HOST, url)

class SignupView(SakaiView):
    def handle_GET(self, request, context, opener, site=None, event_id=None):
        if site and event_id:
            return self.handle_event(request, context, opener, site, event_id)
        if site:
            return self.handle_with_site(request, context, opener, site)
        else:
            return self.handle_without_site(request, context, opener)

    def handle_event(self, request, context, opener, site, event_id):
        url = self.build_url('direct/signupEvent/%s.json?siteId=%s' % (event_id, site))
        event = simplejson.load(opener.open(url))
        
        context.update({
            'event': event,
        })
        return mobile_render(request, context, 'sakai/signup_detail')
        
            
    def handle_with_site(self, request, context, opener, site):
        url = self.build_url('direct/signupEvent/site/%s.xml' % site)
        events_et = ET.parse(opener.open(url)).getroot().findall('signupEvent')
        events = {}
        for event_et in events_et:
            event = {
                'start': parse_iso_8601(event_et.find('startTime').attrib['date']),
                'end': parse_iso_8601(event_et.find('endTime').attrib['date']),
                'location': event_et.find('location').text,
                'title': event_et.find('title').text,
                'id': event_et.find('id').text,
            }
            events[event['id']] = event
        
        context.update({
            'events': events,
            'site': site,
        })
        return mobile_render(request, context, 'sakai/signup_list')
        
    
    def handle_without_site(self, request, context, opener):
        sites = ET.parse(opener.open(self.build_url('direct/site.xml')))
        context['sites'] = [
            (e.find('id').text, e.find('entityTitle').text)
            for e in sites.getroot()
        ]
        return mobile_render(request, context, 'sakai/signup_sites')
    
    def handle_POST(self, request, context, opener, site=None, event_id=None):
        if not site and event:
            return self.method_not_acceptable(request)
            
        response = opener.open(
            self.build_url('direct/signupEvent/%s/edit' % event_id), 
            data = urllib.urlencode({
            'siteId': site,
            'allocToTSid': request.POST['timeslot_id'],
            'userActionType': request.POST['action'],
        }))
        
        print response.getcode()
        print {
            'siteId': site,
            'allocToTSid': request.POST['timeslot_id'],
            'userActionType': request.POST['action'],
        }
        
        return HttpResponseRedirect(request.path)
                
class SiteView(SakaiView):
    def handle_GET(self, request, context, opener):
        sites = ET.parse(opener.open(self.build_url('direct/site.xml')))
        context['sites'] = [e.find('entityTitle').text for e in sites.getroot()]
        return mobile_render(request, context, 'sakai/sites')