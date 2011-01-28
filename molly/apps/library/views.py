from django.core.paginator import Paginator
from django.http import Http404

from molly.utils.views import BaseView
from molly.utils.breadcrumbs import *

from molly.apps.library.forms import SearchForm
from molly.apps.library.models import LibrarySearchQuery

class IndexView(BaseView):
    """
    Index page of the library app
    """
    
    def get_metadata(self, request):
        return {
            'title': 'Library search',
            'additional': "View libraries' contact information and find library items.",
        }
    
    def initial_context(self, request):
        return {
            'search_form': SearchForm()
        }
    
    @BreadcrumbFactory
    def breadcrumb(self, request, context):
        return Breadcrumb(self.conf.local_name, None, 'Library search', lazy_reverse('index'))
    
    def handle_GET(self, request, context):
        return self.render(request, context, 'library/index')

class SearchDetailView(BaseView):
    """
    Search results page
    """
    
    def get_metadata(self, request):
        return {
            'show_in_results': False,
        }
    
    def initial_context(self, request):
        return {
            'search_form': SearchForm(request.GET),
        }
    
    @BreadcrumbFactory
    def breadcrumb(self, request, context):
        if 'item' in context or context['search_form'].is_valid():
            title = 'Search Results'
        else:
            title = 'Library search'
        return Breadcrumb(
            self.conf.local_name,
            lazy_parent('index'),
            title,
            lazy_reverse('search'),
        )
    
    def handle_GET(self, request, context):
        search_form = context['search_form']
        
        if not (request.GET and search_form.is_valid()):
            # No form data received
            return self.render(request, context, 'library/item_list')
        
        # Build a query object to pass to providers here
        try:
            query = LibrarySearchQuery(
                search_form.cleaned_data['title'],
                search_form.cleaned_data['author'],
                search_form.cleaned_data['isbn']
            )
        except LibrarySearchQuery.InconsistentQuery, e:
            return self.handle_error(request, context, e.msg)
        
        # Call provider
        results = self.conf.provider.library_search(query)
        
        # Paginate results
        paginator = Paginator(results, 10)
        
        try:
            page_index = int(request.GET['page'])
        except (ValueError, KeyError):
            page_index = 1
        else:
            page_index = min(max(1, page_index), paginator.num_pages)
        
        page = paginator.page(page_index)
        
        # Render results page
        context.update({
            'removed': query.removed,
            'results': paginator,
            'page': page,
        })
        return self.render(request, context, 'library/item_list')
    
    def handle_error(self, request, context, message):
        context['error_message'] = message
        return self.render(request, context, 'library/item_list')

AVAIL_COLORS = ['red', 'amber', 'purple', 'blue', 'green']

class ItemDetailView(BaseView):
    """
    More detail about the item page
    """
    
    def initial_context(self, request, control_number):
        item = self.conf.provider.control_number_search(control_number)
        print item
        if item is None:
            raise Http404

        return {
            'item': item,
            'control_number': control_number,
        }

    @BreadcrumbFactory
    def breadcrumb(self, request, context, control_number):
        return Breadcrumb(
            self.conf.local_name,
            lazy_parent('search'),
            'Search result',
            lazy_reverse('item-detail', args=[control_number]),
        )

    def handle_GET(self, request, context, control_number):
        return self.render(request, context, 'library/item_detail')

class ItemHoldingsView(BaseView):
    """
    Specific details of holdings of a particular item
    """
    
    def initial_context(cls, request, control_number, sublocation):
        items = search.ControlNumberSearch(control_number, cls.conf)
        if len(items) == 0:
             raise Http404
        item = items[0]

        try:
            library = [l for l in item.libraries if l.location[1] == sublocation][0]
        except IndexError:
            raise Http404

        return {
            'zoom': cls.get_zoom(request),
            'item': item,
            'library': library,
            'control_number': control_number,
            'books': item.libraries[library],
        }

    def get_metadata(cls, request, control_number, sublocation):
        return {
            'show_in_results': False,
        }

    @BreadcrumbFactory
    def breadcrumb(cls, request, context, control_number, sublocation):
        return Breadcrumb(
            cls.conf.local_name,
            lazy_parent('item-detail', control_number=control_number),
            'Item holdings information',
            lazy_reverse('item-holdings-detail', args=[control_number,sublocation]),
        )

    def handle_GET(cls, request, context, control_number, sublocation):
        return cls.render(request, context, 'z3950/item_holdings_detail')
