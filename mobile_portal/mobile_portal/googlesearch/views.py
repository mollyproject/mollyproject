from mobile_portal.core.handlers import BaseView
from mobile_portal.core.renderers import mobile_render

from search import GoogleSearch
from forms import GoogleSearchForm

class GoogleSearchView(BaseView):
    def initial_context(self, request):
        return {
            'search_form': GoogleSearchForm(request.GET or None)
        }
        
    def handle_GET(self, request, context):
        if 'query' in request.GET:
            return self.handle_search(request, request.GET['query'], context)
        
        return mobile_render(request, context, 'googlesearch/index')
        
    def handle_search(self, request, query, context):
        results = GoogleSearch('m.ox.ac.uk', None, query)
        
        context.update({
            'results': list(results)[:20],
        })
        
        return mobile_render(request, context, 'googlesearch/index')