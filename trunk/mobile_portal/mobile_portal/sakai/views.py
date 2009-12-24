from datetime import datetime
import oauth.oauth as oauth
import urllib, urllib2, base64, pytz, simplejson
from xml.etree import ElementTree as ET
import xml.utils.iso8601

from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from django.conf import settings

from mobile_portal.utils.views import BaseView
from mobile_portal.utils.breadcrumbs import *
from mobile_portal.utils.renderers import mobile_render

from mobile_portal.secure.views import OAuthView

from .clients import SakaiOAuthClient

def parse_iso_8601(s):
    return datetime.fromtimestamp(xml.utils.iso8601.parse(s)).replace(tzinfo=pytz.utc)

class IndexView(BaseView):

    @BreadcrumbFactory
    def breadcrumb(cls, request, context):
        return Breadcrumb(
            'sakai',
            None,
            'WebLearn',
            lazy_reverse('sakai_index'),
        )
        
    def handle_GET(cls, request, context):
        return mobile_render(request, context, 'sakai/index')

class SakaiView(OAuthView):
    breadcrumb = NullBreadcrumb

    consumer_secret = settings.SAKAI_CONSUMER_SECRET
    access_token_name = 'sakai_access_token'
    client = SakaiOAuthClient
    signature_method = oauth.OAuthSignatureMethod_PLAINTEXT()
    service_name = 'WebLearn'

    def build_url(cls, url):
        return '%s%s' % (settings.SAKAI_HOST, url)

class SignupIndexView(SakaiView):
    def initial_context(cls, request, opener):
        sites = ET.parse(opener.open(cls.build_url('direct/site.xml')))
        return {
            'sites': [
                (e.find('id').text, e.find('entityTitle').text)
                for e in sites.getroot()
            ],
        }

    @BreadcrumbFactory
    def breadcrumb(cls, request, context, opener):
        return Breadcrumb(
            'sakai',
            lazy_parent(IndexView),
            'Tutorial sign-ups',
            lazy_reverse('sakai_signup'),
        )

    def handle_GET(cls, request, context, opener):
        if not 'sakai_site_titles' in request.secure_session:
            request.secure_session['sakai_site_titles'] = {}
        for site_id, title in context['sites']:
            request.secure_session['sakai_site_titles'][site_id] = title
        return mobile_render(request, context, 'sakai/signup_sites')

class SignupSiteView(SakaiView):
    def initial_context(cls, request, opener, site):
        url = cls.build_url('direct/signupEvent/site/%s.xml' % site)
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
        return {
            'site': site,
            'events': events,
            'title': request.secure_session.get('sakai_site_titles', {}).get(site, 'Site'),
        }

    @BreadcrumbFactory
    def breadcrumb(cls, request, context, opener, site):
        return Breadcrumb(
            'sakai',
            lazy_parent(SignupIndexView, opener),
            context.get('title', 'Tutorial sign-ups'),
            lazy_reverse('sakai_signup_site', args=[site]),
        )
        
    def handle_GET(cls, request, context, opener, site):
        return mobile_render(request, context, 'sakai/signup_list')

class SignupEventView(SakaiView):
    def initial_context(cls, request, opener, site, event_id):
        url = cls.build_url('direct/signupEvent/%s.json?siteId=%s' % (event_id, site))
        event = simplejson.load(opener.open(url))
        
        return {
            'event': event,
        }
        
    @BreadcrumbFactory
    def breadcrumb(cls, request, context, opener, site, event_id):
        return Breadcrumb(
            'sakai',
            lazy_parent(SignupSiteView, opener, site),
            context['event']['title'] if 'event' in context else 'Tutorial sign-ups',
            lazy_reverse('sakai_signup_detail', args=[site, event_id]),
        )

    def handle_GET(cls, request, context, opener, site, event_id):
        return mobile_render(request, context, 'sakai/signup_detail')

    def handle_POST(cls, request, context, opener, site, event_id):
        response = opener.open(
            cls.build_url('direct/signupEvent/%s/edit' % event_id), 
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
    def handle_GET(cls, request, context, opener):
        sites = ET.parse(opener.open(cls.build_url('direct/site.xml')))
        context['sites'] = [e.find('entityTitle').text for e in sites.getroot()]
        return mobile_render(request, context, 'sakai/sites')
        
class DirectView(SakaiView):
    @BreadcrumbFactory
    def breadcrumb(cls, request, context, opener):
        return Breadcrumb(
            'sakai',
            lazy_parent(IndexView),
            'User information',
            lazy_reverse('sakai_direct'),
        )
        
    def handle_GET(cls, request, context, opener):
        response = opener.open('http://perch.oucs.ox.ac.uk:8080/direct/user/current.json')
        return HttpResponse(response.read())
