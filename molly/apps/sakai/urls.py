from django.conf.urls.defaults import *

from views import (
    IndexView, SiteView, DirectView,

    SignupIndexView, SignupSiteView, SignupEventView,
    PollIndexView, PollDetailView,
    EvaluationIndexView, EvaluationDetailView,
    AnnouncementView
)

urlpatterns = patterns('',
    (r'^$',
        IndexView, {},
        'index'),

    (r'^signups/$',
        SignupIndexView, {},
        'signup-index'),
    (r'^signups/(?P<site>[^/]+)/$',
        SignupSiteView, {},
        'signup-site'),
    (r'^signups/(?P<site>[^/]+)/(?P<event_id>\d+)/$',
        SignupEventView, {},
        'signup-event'),

    (r'^polls/$',
        PollIndexView, {},
        'poll-index'),
    (r'^polls/(?P<id>\d+)/$',
        PollDetailView, {},
        'poll-detail'),

    (r'^surveys/$',
        EvaluationIndexView, {},
        'evaluation-index'),
    (r'^surveys/(?P<id>\d+)/$',
        EvaluationDetailView, {},
        'evaluation-detail'),

    (r'^announcements/(?P<id>[^/]+)/$',
        AnnouncementView, {},
        'announcement'),

    (r'^sites/$',
        SiteView, {},
        'sites-index'),

    (r'^direct/$',
        DirectView, {},
        'direct-index'),
)
