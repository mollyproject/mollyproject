from datetime import datetime

import urllib, urllib2, pytz, simplejson, urlparse, StringIO
from lxml import etree
import xml.utils.iso8601

from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied

from molly.auth.models import UserIdentifier
from molly.auth.oauth.clients import OAuthHTTPError
from molly.utils.views import BaseView
from molly.utils.breadcrumbs import *
from molly.utils.http import HttpResponseSeeOther
from molly.utils.xslt import transform, add_children_to_context

def parse_iso_8601(s):
    return datetime.fromtimestamp(xml.utils.iso8601.parse(s)).replace(tzinfo=pytz.utc)


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

    def add_user_identifiers(cls, request):
        user_details = simplejson.load(request.urlopen(cls.build_url('direct/user/current.json')))

        for target, identifier in cls.conf.identifiers:
            value = user_details
            for i in identifier:
                if not i in (value or ()):
                    break
                value = value[i]
            else:
                UserIdentifier.set(request.user, target, value)


class IndexView(SakaiView):

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
            'user_details': simplejson.load(request.opener.open(cls.build_url('/direct/user/current.json'))),
            'tools': [{
                'name': tool[0],
                'title': tool[1],
                'url': reverse('sakai:%s-index' % tool[0]),
            } for tool in cls.conf.tools],
        }

    def handle_GET(cls, request, context):
        
        return cls.render(request, context, 'sakai/index')

class SignupIndexView(SakaiView):
    force_auth = True

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
        events = []
        for event_et in events_et:
            event = {
                'start': parse_iso_8601(event_et.find('startTime').attrib['date']),
                'end': parse_iso_8601(event_et.find('endTime').attrib['date']),
                'location': event_et.find('location').text,
                'title': event_et.find('title').text,
                'id': event_et.find('id').text,
            }
            if event['end'] >= datetime.utcnow().replace(tzinfo=pytz.utc):
                events.append(event)     
        return {
            'site': site,
            'events': events,
            'title': cls.get_site_title(request, site),
            'complex_shorten': True,
            'now': datetime.utcnow(),
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
            event = simplejson.load(request.urlopen(url))
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

        return HttpResponseSeeOther(request.path)

class SiteView(SakaiView):
    force_auth = True

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
    force_auth = True

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
    force_auth = True

    @BreadcrumbFactory
    def breadcrumb(cls, request, context):
        return Breadcrumb(
            cls.conf.local_name,
            lazy_parent(IndexView),
            'Surveys',
            lazy_reverse('sakai:evaluation-index'),
        )

    def initial_context(cls, request):
        try:
            url = cls.build_url('direct/eval-evaluation/1/summary')
            summary = etree.parse(request.opener.open(url), parser = etree.HTMLParser(recover=False))
        except urllib2.HTTPError, e:
            if e.code == 404:
                raise Http404
            elif e.code == 403:
                raise PermissionDenied
            else:
                raise

        summary = transform(summary, 'sakai/evaluation/summary.xslt', {'id': id})

        evaluations = []
        for node in summary.findall('evaluation'):
            evaluations.append({
                'title': node.find('title').text,
                'site': node.find('site').text,
                'start': node.find('start').text,
                'end': node.find('end').text,
                'status': node.find('status').text,
                'id': urlparse.parse_qs(urlparse.urlparse(node.find('url').text).query)['evaluationId'][0] if node.find('url') is not None else None,
            })

        return {
            'evaluations': evaluations,
            'submitted': request.GET.get('submitted') == 'true',
        }

    def handle_GET(cls, request, context):
        return cls.render(request, context, 'sakai/evaluation/index')

class EvaluationDetailView(SakaiView):
    def initial_context(cls, request, id):
        url = cls.build_url('direct/eval-evaluation/%s' % id)
        data = request.raw_post_data if request.method == 'POST' else None
        response = request.urlopen(url, data)
        evaluation = etree.parse(response, parser = etree.HTMLParser(recover=False))

        print etree.tostring(evaluation)
        evaluation = transform(evaluation, 'sakai/evaluation/detail.xslt', {'id': id})
        
        print etree.tostring(evaluation)

        # The evaluations tool doesn't give us a non-OK status if we need to authenticate. Instead,
        # we need to check for the login box (handily picked out by the XSL stylesheet).
        if evaluation.find('.//require_auth').text == 'true':
            raise OAuthHTTPError(urllib2.HTTPError(url, 403, 'Authentication required', {}, StringIO.StringIO()))

        context = {
            'evaluation': evaluation,
            'id': id,
            'url': url,
            'response_url': response.geturl(),
        }
        add_children_to_context(evaluation, context)
        print context['state_message']
        return context

    @BreadcrumbFactory
    def breadcrumb(cls, request, context, id):
        if not 'evaluation' in context:
            context = cls.initial_context(request, id)

        return Breadcrumb(
            cls.conf.local_name,
            lazy_parent(EvaluationIndexView),
            context.get('title', 'Survey'),
            lazy_reverse('sakai:evaluation-detail', args=[id]),
        )

    def handle_GET(cls, request, context, id):
        evaluation = context['evaluation']

        if context['state'] == 'forbidden':
            raise PermissionDenied(context.get('state_message'))
        elif context['state'] == 'closed':
            context = {
                'state': 'closed',
                'breadcrumbs': context['breadcrumbs'],
                'id': id,
            }
            return cls.render(request, context, 'sakai/evaluation/closed')

        return cls.render(request, context, 'sakai/evaluation/detail')

    def handle_POST(cls, request, context, id):
        print context['response_url']
        if context['response_url'].startswith(cls.build_url('direct/eval-evaluation/%s/take_eval?' % id)):
            return cls.handle_GET(request, context, id)

        return HttpResponseSeeOther(reverse('sakai:evaluation-index') + '?submitted=true')
