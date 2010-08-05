from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse

from molly.utils.views import BaseView
from molly.utils.breadcrumbs import *
from molly.utils.http import HttpResponseSeeOther

from .models import Idea
from .forms import IdeaForm

class IndexView(BaseView):
    @BreadcrumbFactory
    def breadcrumb(cls, request, context):
        return Breadcrumb(
            cls.conf.local_name,
            None,
            'Feature suggestions',
            lazy_reverse('feature_vote:index'),
        )

    def initial_context(cls, request):
        return {
            'ideas': Idea.objects.all(),
            'form': IdeaForm(request.POST or None),
        }

    def handle_GET(cls, request, context):
        return cls.render(request, context, 'feature_vote/index')

    def handle_POST(cls, request, context):
        form = context['form']

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
