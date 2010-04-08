from datetime import datetime
import oauth.oauth as oauth
import urllib, urllib2, base64, pytz, simplejson
from xml.etree import ElementTree as ET
import xml.utils.iso8601

from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from django.conf import settings

from molly.utils.views import BaseView
from molly.utils.breadcrumbs import *
from molly.utils.renderers import mobile_render

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
            lazy_reverse('sakai:index'),
        )
        
    def handle_GET(cls, request, context):
        return mobile_render(request, context, 'sakai/index')

class SakaiView(BaseView):
    breadcrumb = NullBreadcrumb

    def build_url(cls, url):
        return '%s%s' % (cls.conf.host, url)
        
    def get_site_title(cls, request, id):
        if not 'sakai_site_titles' in request.secure_session:
            request.secure_session['sakai_site_titles'] = {}
        json = simplejson.load(request.opener.open(cls.build_url('direct/site.json')))
        for site in json['site_collection']:
            request.secure_session['sakai_site_titles'][site['id']] = site['title']
        return request.secure_session['sakai_site_titles'].get(id, 'Unknown site(%s)' % id)


class SignupIndexView(SakaiView):
    def initial_context(cls, request):
        sites = ET.parse(request.opener.open(cls.build_url('direct/site.xml')))
        return {
            'sites': [
                (e.find('id').text, e.find('entityTitle').text)
                for e in sites.getroot()
            ],
            'complex_shorten': True,
        }

    @BreadcrumbFactory
    def breadcrumb(cls, request, context):
        return Breadcrumb(
            'sakai',
            lazy_parent(IndexView),
            'Tutorial sign-ups',
            lazy_reverse('sakai:signup'),
        )

    def handle_GET(cls, request, context):
        if not 'sakai_site_titles' in request.secure_session:
            request.secure_session['sakai_site_titles'] = {}
        for site_id, title in context['sites']:
            request.secure_session['sakai_site_titles'][site_id] = title
        return mobile_render(request, context, 'sakai/signup_sites')

class SignupSiteView(SakaiView):
    def initial_context(cls, request, site):
        url = cls.build_url('direct/signupEvent/site/%s.xml' % site)
        events_et = ET.parse(request.opener.open(url)).getroot().findall('signupEvent')
        events = {}
        for event_et in events_et:
            event = {
                'start': parse_iso_8601(event_et.find('startTime').attrib['date']),
                'end': parse_iso_8601(event_et.find('endTime').attrib['date']),
                'location': event_et.find('location').text,
                'title': event_et.find('title').text,
                'id': event_et.find('id').text,
            }
            if event['end'] >= datetime.utcnow().replace(tzinfo=pytz.utc):
                events[event['id']] = event
        return {
            'site': site,
            'events': events,
            'title': cls.get_site_title(request, site),
            'complex_shorten': True,
        }

    @BreadcrumbFactory
    def breadcrumb(cls, request, context, site):
        return Breadcrumb(
            'sakai',
            lazy_parent(SignupIndexView),
            context.get('title', 'Tutorial sign-ups'),
            lazy_reverse('sakai:signup_site', args=[site]),
        )
        
    def handle_GET(cls, request, context, site):
        return mobile_render(request, context, 'sakai/signup_list')

class SignupEventView(SakaiView):
    def initial_context(cls, request, site, event_id):
        try:
            url = cls.build_url('direct/signupEvent/%s.json?siteId=%s' % (event_id, site))
            event = simplejson.load(request.opener.open(url))
        except urllib2.HTTPError, e:
            if e.code == 404:
                raise Http404
            else:
                raise
        
        
        return {
            'event': event,
            'signedUp': any(e['signedUp'] for e in event['signupTimeSlotItems']),
        }
        
    @BreadcrumbFactory
    def breadcrumb(cls, request, context, site, event_id):
        return Breadcrumb(
            'sakai',
            lazy_parent(SignupSiteView, site),
            context['event']['title'] if 'event' in context else 'Tutorial sign-ups',
            lazy_reverse('sakai:signup_detail', args=[site, event_id]),
        )

    def handle_GET(cls, request, context, site, event_id):
        return mobile_render(request, context, 'sakai/signup_detail')

    def handle_POST(cls, request, context, site, event_id):
        try:
            response = request.opener.open(
                cls.build_url('direct/signupEvent/%s/edit' % event_id), 
                data = urllib.urlencode({
                'siteId': site,
                'allocToTSid': request.POST['timeslot_id'],
                'userActionType': request.POST['action'],
            }))
        except urllib2.HTTPError, e:
            if e.code == 204:
                pass
            else:
                raise
        
        print {
            'siteId': site,
            'allocToTSid': request.POST['timeslot_id'],
            'userActionType': request.POST['action'],
            'complex_shorten': True,
        }
        
        return HttpResponseRedirect(request.path)

class SiteView(SakaiView):
    def handle_GET(cls, request, context):
        sites = ET.parse(request.opener.open(cls.build_url('direct/site.xml')))
        context['sites'] = [e.find('entityTitle').text for e in sites.getroot()]
        return mobile_render(request, context, 'sakai/sites')
        
class DirectView(SakaiView):
    @BreadcrumbFactory
    def breadcrumb(cls, request, context):
        return Breadcrumb(
            'sakai',
            lazy_parent(IndexView),
            'User information',
            lazy_reverse('sakai:direct'),
        )
        
    def handle_GET(cls, request, context):
        context['user_details'] = simplejson.load(
            request.opener.open(cls.build_url('/direct/user/current.json')))
        return mobile_render(request, context, 'sakai/direct')
        
class PollIndexView(SakaiView):
    def initial_context(cls, request):
        json = simplejson.load(request.opener.open(cls.build_url('direct/poll.json')))
        polls = []
        for poll in json['poll_collection']:
            poll['title'] = cls.get_site_title(request, poll['siteId'])
            polls.append(poll)
        
        return {
            'polls': polls,
            'complex_shorten': True,
        }

    @BreadcrumbFactory
    def breadcrumb(cls, request, context):
        return Breadcrumb(
            'sakai',
            lazy_parent(IndexView),
            'Polls',
            lazy_reverse('sakai:poll'),
        )

    def handle_GET(cls, request, context):
        return mobile_render(request, context, 'sakai/poll_index')

class PollDetailView(SakaiView):
    def initial_context(cls, request, id):
        try:
            url = cls.build_url('direct/poll/%s.json' % id)
            poll = simplejson.load(request.opener.open(url))
        except urllib2.HTTPError, e:
            if e.code == 404:
                raise Http404
            else:
                raise
        
        url = cls.build_url('direct/poll/%s/option.json' % id)
        options = simplejson.load(request.opener.open(url))
        
        return {
            'poll': poll,
            'options': options['poll-option_collection'],
            'site_title': cls.get_site_title(request, poll['siteId']),
        }
        
    @BreadcrumbFactory
    def breadcrumb(cls, request, context, opener, id):
        return Breadcrumb(
            'sakai',
            lazy_parent(PollIndexView, opener),
            "Poll: %s" % context['poll']['text'],
            lazy_reverse('sakai:poll_detail'),
        )
        
    def handle_GET(cls, request, context, opener, id):
        return mobile_render(request, context, 'sakai/poll_detail')
