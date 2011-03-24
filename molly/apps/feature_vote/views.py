import random

from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.http import HttpResponseForbidden

from molly.utils.views import BaseView
from molly.utils.breadcrumbs import *
from molly.utils import send_email

from .models import Feature
from .forms import FeatureForm


class IndexView(BaseView):
    # A mapping from (old, new) to (delta down, delta up)
    vote_transitions = {
        (-1,-1) : ( 0, 0),  ( 0,-1): (+1, 0),  (+1,-1): (+1,-1),
        (-1, 0) : (-1, 0),  ( 0, 0): ( 0, 0),  (+1, 0): ( 0,-1),
        (-1,+1) : (-1,+1),  ( 0,+1): ( 0,+1),  (+1,+1): ( 0, 0),
    }
    #  ++    -
    # -      -
    # -    ++
    @BreadcrumbFactory
    def breadcrumb(self, request, context):
        return Breadcrumb(
            self.conf.local_name,
            None,
            'Feature suggestions',
            lazy_reverse('index'),
        )

    def initial_context(self, request):
        if not 'feature_vote:csrf' in request.session:
            request.session['feature_vote:csrf'] = ''.join(random.choice('0123456789abcdef') for i in range(8))
        if not 'feature_vote:votes' in request.session:
            request.session['feature_vote:votes'] = {}

        features = list(Feature.objects.filter(is_public=True))
        for feature in features:
            feature.vote = request.session['feature_vote:votes'].get(feature.id, 0)

        return {
            'features': features,
            'form': FeatureForm(request.POST or None),
            'csrf': request.session['feature_vote:csrf'],
            'submitted': request.GET.get('submitted') == 'true',
        }

    def handle_GET(self, request, context):
        return self.render(request, context, 'feature_vote/index')

    def handle_POST(self, request, context):
        form = context['form']

        if request.POST.get('csrf') != request.session['feature_vote:csrf']:
            return HttpResponseForbidden()

        if 'vote_up' in request.POST or 'vote_down' in request.POST:
            feature = get_object_or_404(Feature, id = request.POST.get('id', 0))
            previous_vote = request.session['feature_vote:votes'].get(feature.id, 0)
            vote = previous_vote + (1 if 'vote_up' in request.POST else -1)
            vote = min(max(-1, vote), 1)
            request.session['feature_vote:votes'][feature.id] = vote
            request.session.modified = True

            feature.down_vote += self.vote_transitions[(previous_vote, vote)][0]
            feature.up_vote += self.vote_transitions[(previous_vote, vote)][1]

            feature.save()

            if request.POST.get('return_url', '').startswith('/'):
                return self.redirect(request.POST['return_url'], request,
                                     'seeother')
            else:
                return self.redirect(reverse('feature_vote:index'), request,
                                     'seeother')

        if form.is_valid():
            form.save()

            send_email(request, {
                'name': form.cleaned_data['user_name'],
                'email': form.cleaned_data['user_email'],
                'title': form.cleaned_data['title'],
                'description': form.cleaned_data['description'],
                'feature': form.instance,
            }, 'feature_vote/feature_create.eml', self)

            return self.redirect(reverse('feature_vote:index') + '?submitted=true',
                                 request, 'seeother')
        else:
            return self.handle_GET(request, context)


class FeatureDetailView(BaseView):

    @BreadcrumbFactory
    def breadcrumb(self, request, context, id):
        return Breadcrumb(
            self.conf.local_name,
            lazy_parent('index'),
            context['feature'].title,
            lazy_reverse('feature-detail'),
        )

    def initial_context(self, request, id):
        if not 'feature_vote:csrf' in request.session:
            request.session['feature_vote:csrf'] = ''.join(random.choice('0123456789abcdef') for i in range(8))
        if not 'feature_vote:votes' in request.session:
            request.session['feature_vote:votes'] = {}
        feature = get_object_or_404(Feature, id=id, is_public=True)
        feature.vote = request.session['feature_vote:votes'].get(feature.id, 0)
        return {
            'feature': feature,
            'csrf': request.session['feature_vote:csrf'],
        }

    def handle_GET(self, request, context, id):
        return self.render(request, context, 'feature_vote/feature_detail')
