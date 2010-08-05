import random

from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.http import HttpResponseForbidden

from molly.utils.views import BaseView
from molly.utils.breadcrumbs import *
from molly.utils.http import HttpResponseSeeOther

from .models import Idea
from .forms import IdeaForm

class IndexView(BaseView):

    # A mapping from (old, new) to (delta down, delta up)
    vote_transitions = {
        (-1,-1) : ( 0, 0),  ( 0,-1): (+1, 0),  (+1,-1): (+1,-1),
        (-1, 0) : (-1, 0),  ( 0, 0): ( 0, 0),  (+1, 0): ( 0,-1),
        (-1,+1) : (-1,+1),  ( 0,+1): ( 0,+1),  (+1,+1): ( 0, 0),
    }

    @BreadcrumbFactory
    def breadcrumb(cls, request, context):
        return Breadcrumb(
            cls.conf.local_name,
            None,
            'Feature suggestions',
            lazy_reverse('feature_vote:index'),
        )

    def initial_context(cls, request):
        if not 'feature_vote:csrf' in request.session:
            request.session['feature_vote:csrf'] = ''.join(random.choice('0123456789abcdef') for i in range(8))
        if not 'feature_vote:votes' in request.session:
            request.session['feature_vote:votes'] = {}
        return {
            'ideas': Idea.objects.all(),
            'form': IdeaForm(request.POST or None),
            'csrf' : request.session['feature_vote:csrf'],
        }

    def handle_GET(cls, request, context):
        return cls.render(request, context, 'feature_vote/index')

    def handle_POST(cls, request, context):
        form = context['form']

        if request.POST.get('csrf') != request.session['feature_vote:csrf']:
            return HttpResponseForbidden()

        if 'vote_up' in request.POST or 'vote_down' in request.POST:
            idea = get_object_or_404(Idea, id = request.POST.get('id', 0))
            previous_vote = request.session['feature_vote:votes'].get(idea.id, 0)
            vote = 1 if 'vote_up' in request.POST else -1
            request.session['feature_vote:votes'][idea.id] = vote
            request.session.modified = True

            idea.down_vote += cls.vote_transitions[(previous_vote, vote)][0]
            idea.up_vote   += cls.vote_transitions[(previous_vote, vote)][1]

            idea.save()

            return HttpResponseSeeOther(reverse('feature_vote:index'))

        if form.is_valid():
            form.save()
            return HttpResponseSeeOther(reverse('feature_vote:index'))
        else:
            return cls.handle_GET(request, context)



class IdeaDetailView(BaseView):
    @BreadcrumbFactory
    def breadcrumb(cls, request, context, id):
        return Breadcrumb(
            cls.conf.local_name,
            lazy_parent(IndexView),
            context['idea'].title,
            lazy_reverse('feature_vote:idea-detail'),
        )

    def initial_context(cls, request, id):
        return {
            'idea': get_object_or_404(Idea, id=id),
        }

    def handle_GET(cls, request, context, id):
        return cls.render(request, context, 'feature_vote/idea_detail')
