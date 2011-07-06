from datetime import datetime, timedelta
import urllib
import urllib2
import simplejson
import urlparse
from lxml import etree
from dateutil.tz import tzutc
import dateutil.parser
from StringIO import StringIO

from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _

from molly.auth.models import UserIdentifier
from molly.auth.oauth.clients import OAuthHTTPError
from molly.utils.views import BaseView
from molly.utils.breadcrumbs import *
from molly.utils.xslt import transform, add_children_to_context

def parse_iso_8601(s):
    return dateutil.parser.parse(s).replace(tzinfo=tzutc())


class SakaiView(BaseView):
    breadcrumb = NullBreadcrumb
    abstract = True

    def build_url(self, url):
        return '%s%s' % (self.conf.host, url)

    def get_site_title(self, request, id):
        if not 'sakai_site_titles' in request.secure_session:
            request.secure_session['sakai_site_titles'] = {}
        json = simplejson.load(request.opener.open(self.build_url('direct/site.json')))
        for site in json['site_collection']:
            request.secure_session['sakai_site_titles'][site['id']] = site['title']
        return request.secure_session['sakai_site_titles'].get(id, 'Unknown site(%s)' % id)

    def add_user_identifiers(self, request):
        user_details = simplejson.load(request.urlopen(self.build_url('direct/user/current.json')))

        for target, identifier in self.conf.identifiers:
            value = user_details
            for i in identifier:
                if not i in (value or ()):
                    break
                value = value[i]
            else:
                UserIdentifier.set(request.user, target, value)


class IndexView(SakaiView):

    @BreadcrumbFactory
    def breadcrumb(self, request, context):
        # TODO Remove 'WebLearn' as the standard name for Sakai 
        return Breadcrumb(
            self.conf.local_name,
            None,
            _('WebLearn'),
            lazy_reverse('index'),
        )

    def initial_context(self, request): 
        return {
            'user_details': simplejson.load(request.opener.open(self.build_url('/direct/user/current.json'))),
            'announcements': simplejson.load(request.opener.open(self.build_url('/direct/announcement/user.json'))),
            'tools': [{
                'name': tool[0],
                'title': tool[1],
                'url': reverse('sakai:%s-index' % tool[0]),
            } for tool in self.conf.tools],
        }

    def handle_GET(self, request, context):
        
        if 'force_login' in request.GET:
            if len(context['user_details']['id']) == 0:
                # pretend we got a 401 error, this will force the auth framework
                # to reauthenticate
                raise OAuthHTTPError(urllib2.HTTPError('', 401, '', '', StringIO()))
        
        return self.render(request, context, 'sakai/index', expires=timedelta(days=-1))

class SignupIndexView(SakaiView):
    force_auth = True

    def initial_context(self, request):
        sites = simplejson.load(request.opener.open(self.build_url('direct/site.json')))
        return {
            'sites': [
                (e['id'], e['entityTitle'])
                for e in sites['site_collection']
            ],
            'complex_shorten': True,
        }

    @BreadcrumbFactory
    def breadcrumb(self, request, context):
        return Breadcrumb(
            self.conf.local_name,
            lazy_parent('index'),
            _('Sign-ups'),
            lazy_reverse('signup-index'),
        )

    def handle_GET(self, request, context):
        if not 'sakai_site_titles' in request.secure_session:
            request.secure_session['sakai_site_titles'] = {}
        for site_id, title in context['sites']:
            request.secure_session['sakai_site_titles'][site_id] = title
        return self.render(request, context, 'sakai/signup/index', expires=timedelta(days=-1))

class SignupSiteView(SakaiView):
    def initial_context(self, request, site):
        url = self.build_url('direct/signupEvent/site/%s.xml' % site)
        events_et = etree.parse(request.opener.open(url)).getroot().findall('signupEvent')
        events = []
        for event_et in events_et:
            event = {
                'start': parse_iso_8601(event_et.find('startTime').attrib['date']),
                'end': parse_iso_8601(event_et.find('endTime').attrib['date']),
                'location': event_et.find('location').text,
                'title': event_et.find('title').text,
                'id': event_et.find('id').text,
                'permission': dict((p.tag, p.text=='true') for p in event_et.findall('permission/*'))
            }
            if event['end'] >= datetime.utcnow().replace(tzinfo=tzutc()):
                events.append(event)     
        return {
            'site': site,
            'events': events,
            'title': self.get_site_title(request, site),
            'complex_shorten': True,
            'now': datetime.utcnow(),
        }

    @BreadcrumbFactory
    def breadcrumb(self, request, context, site):
        return Breadcrumb(
            self.conf.local_name,
            lazy_parent('signup-index'),
            context.get('title', 'Sign-ups'),
            lazy_reverse('signup-site', args=[site]),
        )

    def handle_GET(self, request, context, site):
        return self.render(request, context, 'sakai/signup/list', expires=timedelta(days=-1))

class SignupEventView(SakaiView):
    def initial_context(self, request, site, event_id):
        try:
            # This request does absolutely nothing, except force some cache to be
            # reset, making sure the data we receive subsequently is up-to-date.
            # This should be reported as a bug in Sakai.
            request.urlopen(
                self.build_url('direct/signupEvent/%s/edit' % event_id),
                data = urllib.urlencode({
                'siteId': site,
                'allocToTSid': '0',
                'userActionType': 'invalidAction',
            }))
    
            url = self.build_url('direct/signupEvent/%s.json?siteId=%s' % (event_id, site))
            event = simplejson.load(request.urlopen(url))
        except PermissionDenied, e:
            if isinstance(e, OAuthHTTPError) and e.code != 403:
                raise
            else:
                context = {
                    'permission_denied': True,
                    'text': _('Permission Denied')
                }
                return context
        
        return {
            'event': event,
            'signedUp': any(e['signedUp'] for e in event['signupTimeSlotItems']),
        }

    @BreadcrumbFactory
    def breadcrumb(self, request, context, site, event_id):
        return Breadcrumb(
            self.conf.local_name,
            lazy_parent('signup-site', site),
            context['event']['title'] if 'event' in context else 'Sign-ups',
            lazy_reverse('signup-detail', args=[site, event_id]),
        )

    def handle_GET(self, request, context, site, event_id):
        if 'permission_denied' in context:
            response = render_to_response('sakai/permission_denied.html',
                                          RequestContext(request, context))
            response.status_code = 403
            return response
        return self.render(request, context, 'sakai/signup/detail', expires=timedelta(days=-1))

    def handle_POST(self, request, context, site, event_id):
        try:
            response = request.opener.open(
                self.build_url('direct/signupEvent/%s/edit' % event_id),
                data = urllib.urlencode({
                'siteId': site,
                'allocToTSid': request.POST['timeslot_id'],
                'userActionType': request.POST['action'],
            }))
        except urllib2.HTTPError, e:
            if e.code != 204:
                raise

        return self.redirect(request.path, request, 'seeother')

class SiteView(SakaiView):
    force_auth = True

    def handle_GET(self, request, context):
        sites = etree.parse(request.opener.open(self.build_url('direct/site.xml')))
        context['sites'] = [e.find('entityTitle').text for e in sites.getroot()]
        return self.render(request, context, 'sakai/sites', expires=timedelta(days=-1))

class DirectView(SakaiView):
    @BreadcrumbFactory
    def breadcrumb(self, request, context):
        return Breadcrumb(
            self.conf.local_name,
            lazy_parent('index'),
            _('User information'),
            lazy_reverse('direct-index'),
        )

    def handle_GET(self, request, context):
        context['user_details'] = simplejson.load(
            request.opener.open(self.build_url('/direct/user/current.json')))
        return self.render(request, context, 'sakai/direct/index', expires=timedelta(days=-1))

def annotate_poll(poll):
    """
    Annotates a poll object as returned from Sakai with some useful derived information.
    """
    poll['voteOpen'] = datetime.fromtimestamp(poll['voteOpen']/1000)
    poll['voteClose'] = datetime.fromtimestamp(poll['voteClose']/1000)
    poll.update({
        'multiVote': poll['maxOptions'] > 1,
        'hasOpened': datetime.now() > poll['voteOpen'],
        'hasClosed': datetime.now() > poll['voteClose'],
        'hasVoted': bool(poll['currentUserVotes']),
    })
    poll['isOpen'] = poll['hasOpened'] and not poll['hasClosed']
    poll['mayVote'] = poll['isOpen'] and not poll['hasVoted']

class PollIndexView(SakaiView):
    force_auth = True

    def initial_context(self, request):
        json = simplejson.load(request.opener.open(self.build_url('direct/poll.json')))
        polls = []
        for poll in json['poll_collection']:
            poll['siteTitle'] = self.get_site_title(request, poll['siteId'])
            annotate_poll(poll)
            polls.append(poll)
        polls.sort(key=lambda p:(p['siteTitle'], p['voteClose']))

        return {
            'polls': polls,
            'complex_shorten': True,
        }

    @BreadcrumbFactory
    def breadcrumb(self, request, context):
        return Breadcrumb(
            self.conf.local_name,
            lazy_parent('index'),
            'Polls',
            lazy_reverse('poll-index'),
        )

    def handle_GET(self, request, context):
        return self.render(request, context, 'sakai/poll/index', expires=timedelta(days=-1))

class PollDetailView(SakaiView):
    def initial_context(self, request, id):
        
        try:
            url = self.build_url('direct/poll/%s.json' % id)
            poll = simplejson.load(request.urlopen(url))
    
            url = self.build_url('direct/poll/%s/option.json' % id)
            options = simplejson.load(request.urlopen(url))
            options = options['poll-option_collection']
        except PermissionDenied, e:
            if isinstance(e, OAuthHTTPError) and e.code != 403:
                raise
            else:
                context = {
                    'poll': {
                        'permission_denied': True,
                        'text': _('Permission Denied')
                    }
                }
                return context

        try:
            url = self.build_url('direct/poll/%s/vote.json' % id)
            votes = simplejson.load(request.urlopen(url))
            votes = votes["poll-vote_collection"]
        except PermissionDenied:
            max_votes, vote_count = None, None
        
        else:
            pollOptions, max_votes, vote_count = {}, 0, len(votes)
            for option in options:
                option['voteCount'] = 0
                pollOptions[option['optionId']] = option
            for vote in votes:
                pollOptions[vote['pollOption']]['voteCount'] += 1
                max_votes = max(max_votes, pollOptions[vote['pollOption']]['voteCount'])

        # Add votedFor attributes if the user voted for any given option
        userVotes =  [vote['pollOption'] for vote in poll['currentUserVotes']]
        for option in options:
            option['votedFor'] = option['optionId'] in userVotes

        annotate_poll(poll)

        return {
            'poll': poll,
            'options': options,
            'site_title': self.get_site_title(request, poll['siteId']),
            'max_votes': max_votes,
            'vote_count': vote_count,
            'sakai_host': self.conf.host,
            'service_name': self.conf.service_name,
        }

    @BreadcrumbFactory
    def breadcrumb(self, request, context, id):
        return Breadcrumb(
            self.conf.local_name,
            lazy_parent('poll-index'),
            context['poll']['text'],
            lazy_reverse('poll-detail'),
        )

    def handle_GET(self, request, context, id):
        if 'permission_denied' in context['poll']:
            response = render_to_response('sakai/permission_denied.html',
                                          RequestContext(request, context))
            response.status_code = 403
            return response
        return self.render(request, context, 'sakai/poll/detail', expires=timedelta(days=-1))

    def handle_POST(self, request, context, id):
        if not context['poll']['mayVote']:
            return self.redirect(request.path, request, 'seeother')
        
        # Check poll boundaries
        if len(request.POST.getlist('pollOption')) > context['poll']['maxOptions'] or \
           len(request.POST.getlist('pollOption')) < context['poll']['minOptions']:
            context['error'] = 'You must select between %d and %d options' % (context['poll']['minOptions'], context['poll']['maxOptions'])
            return self.handle_GET(request, context, id)
        try:
            data = [('pollId', int(id))]
            for option in request.POST.getlist('pollOption'):
                if not int(option) in (option['optionId'] for option in context['options']):
                    return HttpResponseBadRequest()
                data.append(('pollOption', int(option)))
            response = request.opener.open(
                self.build_url('direct/poll-vote/%s' % ('vote.json' if len(request.POST.getlist('pollOption')) > 1 else 'new')),
                data = urllib.urlencode(data)
            )
        except urllib2.HTTPError, e:
            if e.code in (201, 204):
                pass
            else:
                raise

        return self.redirect(request.path, request, 'seeother')

class EvaluationIndexView(SakaiView):
    force_auth = True

    @BreadcrumbFactory
    def breadcrumb(self, request, context):
        return Breadcrumb(
            self.conf.local_name,
            lazy_parent('index'),
            _('Surveys'),
            lazy_reverse('evaluation-index'),
        )

    def initial_context(self, request):
        url = self.build_url('direct/eval-evaluation/1/summary')
        summary = etree.parse(request.opener.open(url), parser = etree.HTMLParser(recover=False))
        summary = transform(summary, 'sakai/evaluation/summary.xslt', {'id': id})
        evaluations = []
        for node in summary.findall('evaluation'):
            if not node.find('title').text is None:
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
        }

    def handle_GET(self, request, context):
        return self.render(request, context, 'sakai/evaluation/index', expires=timedelta(days=-1))

class EvaluationDetailView(SakaiView):
    
    def initial_context(self, request, id):
        url = self.build_url('direct/eval-evaluation/%s' % id)
        data = request.raw_post_data if request.method == 'POST' else None
        response = request.urlopen(url, data)
        evaluation = etree.parse(response, parser = etree.HTMLParser(recover=False))
        evaluation = transform(evaluation, 'sakai/evaluation/detail.xslt', {'id': id})

        # The evaluations tool doesn't give us a non-OK status if we need to authenticate. Instead,
        # we need to check for the login box (handily picked out by the XSL stylesheet).
        if evaluation.find('.//require_auth').text == 'true':
            raise OAuthHTTPError(urllib2.HTTPError(url, 403, _('Authentication required'), {}, StringIO()))

        context = {
            'evaluation': evaluation,
            'id': id,
            'url': url,
            'response_url': response.geturl(),
        }
        add_children_to_context(evaluation, context)
        return context

    @BreadcrumbFactory
    def breadcrumb(self, request, context, id):
        if not 'evaluation' in context:
            context = self.initial_context(request, id)

        return Breadcrumb(
            self.conf.local_name,
            lazy_parent('evaluation-index'),
            context.get('title', 'Survey'),
            lazy_reverse('evaluation-detail', args=[id]),
        )

    def handle_GET(self, request, context, id):
        evaluation = context['evaluation']

        if context['state'] == 'forbidden':
            raise PermissionDenied(context.get('state_message'))
        elif context['state'] == 'closed':
            context = {
                'state': 'closed',
                'breadcrumbs': context['breadcrumbs'],
                'id': id,
            }
            return self.render(request, context, 'sakai/evaluation/closed', expires=timedelta(days=-1))

        return self.render(request, context, 'sakai/evaluation/detail', expires=timedelta(days=-1))

    def handle_POST(self, request, context, id):
        if context['response_url'].startswith(self.build_url('direct/eval-evaluation/%s/take_eval?' % id)):
            return self.handle_GET(request, context, id)
        context = {
            'suppress_evaluations': True,
            'submitted': True,
        }
        return self.render(request, context, 'sakai/evaluation/index', expires=timedelta(days=-1))

class AnnouncementView(SakaiView):
    """
    Displays the detail of an anouncement
    """

    @BreadcrumbFactory
    def breadcrumb(self, request, context, id):
        if not 'announcement' in context:
            context = self.initial_context(request, id)

        return Breadcrumb(
            self.conf.local_name,
            lazy_parent('index'),
            context['announcement']['title'],
            lazy_reverse('announcement', args=[id]),
        )
    
    def initial_context(self, request, id):
        
        response = request.urlopen(self.build_url('direct/announcement/%s.json' % id))
        return {
            'announcement': simplejson.load(response)
        }
    
    def handle_GET(self, request, context, id):
        return self.render(request, context, 'sakai/announcement/detail', expires=timedelta(days=-1))
