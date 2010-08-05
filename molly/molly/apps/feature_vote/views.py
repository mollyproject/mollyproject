from django.shortcuts import get_object_or_404

from molly.utils.views import BaseView
from molly.utils.breadcrumbs import *

from .models import Idea

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
        }

    def handle_GET(cls, request, context):
        return cls.render(request, context, 'feature_vote/index')

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
