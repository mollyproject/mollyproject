from datetime import timedelta

from molly.utils.views import BaseView
from molly.utils.breadcrumbs import *

from forms import SearchForm

class IndexView(BaseView):
    def initial_context(self, request):
        return {
            'search_form': getattr(self.conf, 'form', SearchForm(request.GET or None))
        }

    @BreadcrumbFactory
    def breadcrumb(self, request, context):
        return Breadcrumb(
            'search', None, 'Search', lazy_reverse('index')
        )

    def handle_GET(self, request, context):
        if context['search_form'].is_valid():
            return self.handle_search(request, context)

        return self.render(request, context, 'search/index',
                           expires=timedelta(minutes=30))

    def handle_search(self, request, context):
        application = context['search_form'].cleaned_data['application'] or None
        query = context['search_form'].cleaned_data['query']

        results = []
        for provider in self.conf.providers:
            results += provider.perform_search(request, query, application)

        seen_urls, i = set(), 0
        while i < len(results):
            url = results[i]['url']
            if url in seen_urls:
                results[i:i+1] = []
            else:
                seen_urls.add(url)
                i += 1

        # Remove results deemed irrelevant
        results = [r for r in results if not r.get('exclude_from_search')]

        if len(results) == 1 and results[0].get('redirect_if_sole_result'):
            return self.redirect(results[0]['url'], request)

        context.update({
            'results': list(results)[:20],
        })

        return self.render(request, context, 'search/index')
