from mobile_portal.core.handlers import BaseView
from mobile_portal.core.renderers import mobile_render

from mobile_portal.core.breadcrumbs import Breadcrumb, BreadcrumbFactory, lazy_reverse, lazy_parent, NullBreadcrumb

from search import GoogleSearch
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
        
        results = GoogleSearch('m.ox.ac.uk', application, query, request)
        
        context.update({
            'results': list(results)[:20],
        })
        
        return mobile_render(request, context, 'googlesearch/index')