from datetime import datetime

import urllib, urllib2, pytz, simplejson
from lxml import etree
import xml.utils.iso8601

from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.core.urlresolvers import reverse
from django.template import loader, Context

from molly.utils.views import BaseView
from molly.utils.breadcrumbs import *
from molly.utils.http import HttpResponseSeeOther


def parse_iso_8601(s):
    return datetime.fromtimestamp(xml.utils.iso8601.parse(s)).replace(tzinfo=pytz.utc)

class IndexView(BaseView):

    @BreadcrumbFactory
    def breadcrumb(cls, request, context):
        return Breadcrumb(
            cls.conf.local_name,
            None,
            'WebLearn',
            lazy_reverse('sakai:index'),
        )

    def initial_context(cls, request):
        return {
            'tools': [{
                'name': tool[0],
                'title': tool[1],
                'url': reverse('sakai:%s-index' % tool[0]),
            } for tool in cls.conf.tools],
        }

    def handle_GET(cls, request, context):
        return cls.render(request, context, 'sakai/index')

class SakaiView(BaseView):
    breadcrumb = NullBreadcrumb
    abstract = True

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
        sites = etree.parse(request.opener.open(cls.build_url('direct/site.xml')))
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
            cls.conf.local_name,
            lazy_parent(IndexView),
            'Tutorial sign-ups',
            lazy_reverse('sakai:signup-index'),
        )

    def handle_GET(cls, request, context):
        if not 'sakai_site_titles' in request.secure_session:
            request.secure_session['sakai_site_titles'] = {}
        for site_id, title in context['sites']:
            request.secure_session['sakai_site_titles'][site_id] = title
        return cls.render(request, context, 'sakai/signup/index')

class SignupSiteView(SakaiView):
    def initial_context(cls, request, site):
        url = cls.build_url('direct/signupEvent/site/%s.xml' % site)
        events_et = etree.parse(request.opener.open(url)).getroot().findall('signupEvent')
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
            cls.conf.local_name,
            lazy_parent(SignupIndexView),
            context.get('title', 'Tutorial sign-ups'),
            lazy_reverse('sakai:signup-site', args=[site]),
        )

    def handle_GET(cls, request, context, site):
        return cls.render(request, context, 'sakai/signup/list')

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
            cls.conf.local_name,
            lazy_parent(SignupSiteView, site),
            context['event']['title'] if 'event' in context else 'Tutorial sign-ups',
            lazy_reverse('sakai:signup-detail', args=[site, event_id]),
        )

    def handle_GET(cls, request, context, site, event_id):
        return cls.render(request, context, 'sakai/signup/detail')

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

        return HttpResponseSeeOther(request.path)

class SiteView(SakaiView):
    def handle_GET(cls, request, context):
        sites = etree.parse(request.opener.open(cls.build_url('direct/site.xml')))
        context['sites'] = [e.find('entityTitle').text for e in sites.getroot()]
        return cls.render(request, context, 'sakai/sites')

class DirectView(SakaiView):
    @BreadcrumbFactory
    def breadcrumb(cls, request, context):
        return Breadcrumb(
            cls.conf.local_name,
            lazy_parent(IndexView),
            'User information',
            lazy_reverse('sakai:direct-index'),
        )

    def handle_GET(cls, request, context):
        context['user_details'] = simplejson.load(
            request.opener.open(cls.build_url('/direct/user/current.json')))
        return cls.render(request, context, 'sakai/direct/index')

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
            cls.conf.local_name,
            lazy_parent(IndexView),
            'Polls',
            lazy_reverse('sakai:poll-index'),
        )

    def handle_GET(cls, request, context):
        return cls.render(request, context, 'sakai/poll/index')

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
    def breadcrumb(cls, request, context, id):
        return Breadcrumb(
            cls.conf.local_name,
            lazy_parent(PollIndexView),
            "Poll: %s" % context['poll']['text'],
            lazy_reverse('sakai:poll-detail'),
        )

    def handle_GET(cls, request, context, id):
        return cls.render(request, context, 'sakai/poll/detail')

    def handle_POST(cls, request, context, id):
        print simplejson.dumps({
                    'pollId': int(id),
                    'pollOption': int(request.POST['pollOption']),
            })

        try:
            response = request.opener.open(
                cls.build_url('direct/poll-vote/new'), 
                data = simplejson.dumps({
                    'pollId': int(id),
                    'pollOption': int(request.POST['pollOption']),
            }))
        except urllib2.HTTPError, e:
            return HttpResponse(e.read(), mimetype="text/html")
            if e.code == 204:
                pass
            else:
                raise

        return HttpResponseSeeOther(request.path)

class EvaluationIndexView(SakaiView):
    breadcrumb = NullBreadcrumb

    def handle_GET(cls, request, context):
        raise Http404

class EvaluationDetailView(SakaiView):
    breadcrumb = NullBreadcrumb

    def initial_context(cls, request, id):
        try:
            url = cls.build_url('direct/eval-evaluation/%s' % id)
            evaluation = etree.parse(request.opener.open(url), parser = etree.HTMLParser(recover=False))
        except urllib2.HTTPError, e:
            print e.getcode()
            if e.code == 404:
                raise Http404
            else:
                raise

        xslt_doc = loader.get_template('sakai/evaluation/detail.xslt')
        xslt_doc = etree.XSLT(etree.fromstring(xslt_doc.render(Context({'id':id}))))
        evaluation = xslt_doc(evaluation)

        context = {
            'evaluation': evaluation,
            'id': id,
            'url': url,
        }
        print etree.tostring(evaluation)
        for node in evaluation.findall('*'):
            context[node.tag] = etree.tostring(node, method="html")[len(node.tag)+2:-len(node.tag)-3]

        return context

    @BreadcrumbFactory
    def breadcrumb(cls, request, context, id):
        if not 'evaluation' in context:
            context = EvaluationDetailView.initial_context(request, id)

        return Breadcrumb(
            cls.conf.local_name,
            None,
            context['title'],
            lazy_reverse('sakai:evaluation-detail', args=[id]),
        )

    def handle_GET(cls, request, context, id):
        evaluation = context['evaluation']

        if context['state'] == 'forbidden':
            return HttpResponseForbidden()
        elif context['state'] == 'closed':
            context = {
                'state': 'closed',
                'breadcrumbs': context['breadcrumbs'],
                'id': id,
            }
            return cls.render(request, context, 'sakai/evaluation/closed')

        print context.keys()

        return cls.render(request, context, 'sakai/evaluation/detail')

    def handle_POST(cls, request, context, id):
        response = request.opener.open(context['url'], request.POST)       

        print response.geturl()

        context.update({
            'body': response.read(),
        })

        return cls.render(request, context, None)

class EvaluationSummaryView(SakaiView):
    breadcrumb = NullBreadcrumb

    def handle_GET(cls, request, context, id):
        url = cls.build_url('direct/eval-evaluation/%s/summary' % id)
        if 'QUERY_STRING' in request.META:
            url += '?%s' % request.META['QUERY_STRING']
        request.opener.open(url)

