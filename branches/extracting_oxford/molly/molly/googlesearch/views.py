from django.http import HttpResponseRedirect

from molly.utils.views import BaseView
from molly.utils.renderers import mobile_render
from molly.utils.breadcrumbs import *

from search import GoogleSearch, OverrideResponse
from forms import GoogleSearchForm

class GoogleSearchView(BaseView):
    def initial_context(cls, request):
        return {
            'search_form': GoogleSearchForm(request.GET or None)
        }

    @BreadcrumbFactory
    def breadcrumb(cls, request, context):
        return Breadcrumb(
            'googlesearch', None, 'Search', lazy_reverse('googlesearch_index')
        )
        
    def handle_GET(cls, request, context):
        if context['search_form'].is_valid():
            return cls.handle_search(request, context)
        
        return mobile_render(request, context, 'googlesearch/index')
        
    def handle_search(cls, request, context):
        application = context['search_form'].cleaned_data['application'] or None
        query = context['search_form'].cleaned_data['query']
        
        try:
            results = list(GoogleSearch('m.ox.ac.uk', application, query, request))
        except OverrideResponse, e:
            return e.response
            
        if len(results) == 1 and results[0].get('redirect_if_sole_result'):
            return HttpResponseRedirect(results[0]['url'])
        
        context.update({
            'results': list(results)[:20],
        })
        
        return mobile_render(request, context, 'googlesearch/index')