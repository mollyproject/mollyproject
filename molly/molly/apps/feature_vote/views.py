import random

from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.http import HttpResponseForbidden

from molly.utils.views import BaseView
from molly.utils.breadcrumbs import *
from molly.utils.http import HttpResponseSeeOther
from molly.utils.email import send_email

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
            'features': Feature.objects.all(),
            'form': FeatureForm(request.POST or None),
            'csrf' : request.session['feature_vote:csrf'],
            'submitted': request.GET.get('submitted') == 'true',
        }

    def handle_GET(cls, request, context):
        return cls.render(request, context, 'feature_vote/index')

    def handle_POST(cls, request, context):
        form = context['form']

        if request.POST.get('csrf') != request.session['feature_vote:csrf']:
            return HttpResponseForbidden()

        if 'vote_up' in request.POST or 'vote_down' in request.POST:
            feature = get_object_or_404(Feature, id = request.POST.get('id', 0))
            previous_vote = request.session['feature_vote:votes'].get(feature.id, 0)
            vote = 1 if 'vote_up' in request.POST else -1
            request.session['feature_vote:votes'][feature.id] = vote
            request.session.modified = True

            feature.down_vote += cls.vote_transitions[(previous_vote, vote)][0]
            feature.up_vote   += cls.vote_transitions[(previous_vote, vote)][1]

            feature.save()

            return HttpResponseSeeOther(reverse('feature_vote:index'))

        if form.is_valid():
            form.save()

            send_email(request, {
                'name': form.cleaned_data['user_name'],
                'email': form.cleaned_data['user_email'],
                'title': form.cleaned_data['title'],
                'description': form.cleaned_data['description'],
                'feature': form.instance,
            }, 'feature_vote/feature_create.eml', cls)
            
            return HttpResponseSeeOther(reverse('feature_vote:index') + '?submitted=true')
        else:
            return cls.handle_GET(request, context)



class FeatureDetailView(BaseView):
    @BreadcrumbFactory
    def breadcrumb(cls, request, context, id):
        return Breadcrumb(
            cls.conf.local_name,
            lazy_parent(IndexView),
            context['feature'].title,
            lazy_reverse('feature_vote:feature-detail'),
        )

    def initial_context(cls, request, id):
        return {
            'feature': get_object_or_404(Feature, id=id, is_public=True),
        }

    def handle_GET(cls, request, context, id):
        return cls.render(request, context, 'feature_vote/feature_detail')
