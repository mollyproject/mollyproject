from django.http import HttpResponseRedirect

from molly.utils.views import BaseView
from molly.utils.breadcrumbs import *

from forms import SearchForm

class GoogleSearchView(BaseView):
    def initial_context(cls, request):
        return {
            'search_form': getattr(cls.conf, 'form', SearchForm(request.GET or None))
        }

    @BreadcrumbFactory
    def breadcrumb(cls, request, context):
        return Breadcrumb(
            'search', None, 'Search', lazy_reverse('search:index')
        )

    def handle_GET(cls, request, context):
        if context['search_form'].is_valid():
            return cls.handle_search(request, context)

        return cls.render(request, context, 'search/index')

    def handle_search(cls, request, context):
        application = context['search_form'].cleaned_data['application'] or None
        query = context['search_form'].cleaned_data['query']

        results = []
        for provider in cls.conf.providers:
            results += provider.perform_search(request, query, application)
        
        # Remove results deemed irrelevant
        results = [r for r in results if not r.get('exclude_from_search')]
        
        if len(results) == 1 and results[0].get('redirect_if_sole_result'):
            return HttpResponseRedirect(results[0]['url'])

        context.update({
            'results': list(results)[:20],
        })

        return cls.render(request, context, 'search/index')
