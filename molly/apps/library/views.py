from datetime import timedelta

from django.core.paginator import Paginator
from django.http import Http404
from django.utils.translation import ugettext as _

from molly.utils import haversine
from molly.utils.views import BaseView, ZoomableView
from molly.utils.breadcrumbs import *
from molly.maps import Map

from molly.apps.library.forms import SearchForm
from molly.apps.library.models import LibrarySearchQuery, LibrarySearchError

class IndexView(BaseView):
    """
    Index page of the library app
    """
    
    def get_metadata(self, request):
        return {
            'title': _('Library search'),
            'additional': _("View libraries' contact information and find library items."),
        }
    
    def initial_context(self, request):
        return {
            'search_form': SearchForm()
        }
    
    @BreadcrumbFactory
    def breadcrumb(self, request, context):
        return Breadcrumb(self.conf.local_name, None, _('Library search'), lazy_reverse('index'))
    
    def handle_GET(self, request, context):
        return self.render(request, context, 'library/index',
                           expires=timedelta(days=28))

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
            title = _('Search Results')
        else:
            title = _('Library search')
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
        try:
            results = self.conf.provider.library_search(query)
        except LibrarySearchError as e:
            return self.handle_error(request, context, e.message)
        
        # Paginate results
        paginator = Paginator(results, 10)
        
        try:
            page_index = int(request.GET['page'])
        except (ValueError, KeyError):
            page_index = 1
        else:
            page_index = min(max(1, page_index), paginator.num_pages)
        
        page = paginator.page(page_index)
        
        # Add cover image
        if hasattr(self.conf, 'additional_metadata_provider'):
            
            self.conf.additional_metadata_provider.annotate(page.object_list)
        
        # Without this, the object_list doesn't render when using fragment
        # rendering...
        page.object_list = list(page.object_list)
        
        # Render results page
        context.update({
            'removed': query.removed,
            'results': paginator,
            'page': page,
        })
        return self.render(request, context, 'library/item_list',
                           expires=timedelta(hours=1))
    
    def handle_error(self, request, context, message):
        context['error_message'] = message
        return self.render(request, context, 'library/item_list')

AVAIL_COLORS = ['red', 'amber', 'purple', 'blue', 'green']

class ItemDetailView(ZoomableView):
    """
    More detail about the item page
    """
    
    def initial_context(self, request, control_number):
        context = super(ItemDetailView, self).initial_context(request)
        item = self.conf.provider.control_number_search(control_number)
        if item is None:
            raise Http404()
        
        context.update({
            'item': item,
            'control_number': control_number,
        })
        return context

    @BreadcrumbFactory
    def breadcrumb(self, request, context, control_number):
        return Breadcrumb(
            self.conf.local_name,
            lazy_parent('search'),
            _('Search result'),
            lazy_reverse('item-detail', args=[control_number]),
        )

    def handle_GET(self, request, context, control_number):
        
        # Build a map of all the libraries that have this book, with markers
        # corresponding to colours
        
        user_location = request.session.get('geolocation:location')
        
        points = []
        point_libraries = []
        lbs = context['item'].libraries.items()
        
        for library, books in lbs:
            library.entity = library.get_entity()

        if user_location:
            lbs = sorted(lbs, key=lambda (l,b): (haversine(user_location, l.entity.location)
                if l.entity and l.entity.location else float('inf')))

        for library, books in lbs:
            if library.entity != None and library.entity.location != None:
                colour = AVAIL_COLORS[max(b['availability'] for b in books)]
                points.append((library.entity.location[0],
                               library.entity.location[1],
                               colour,
                               library.entity.title))
                point_libraries.append(library)
        
        if len(points) > 0:
            context['map'] = Map(
                centre_point = (user_location[0], user_location[1], 'green', '')
                                if user_location != None else None,
                points = points,
                min_points = 0 if context['zoom'] else len(points),
                zoom = context['zoom'],
                width = request.map_width,
                height = request.map_height,
            )
            
            # Yes, this is weird. fit_to_map() groups libraries with the same
            # location so here we add a marker_number to each library to display
            # in the template.
            lib_iter = iter(point_libraries)
            for i, (a,b) in enumerate(context['map'].points):
                for j in range(len(b)):
                    lib_iter.next().marker_number = i + 1
        
        context.update({
            'sorted_libraries': lbs,
        })
        
        return self.render(request, context, 'library/item_detail')

class ItemHoldingsView(ZoomableView):
    """
    Specific details of holdings of a particular item
    """
    
    def initial_context(self, request, control_number, sublocation):
        
        context = super(ItemHoldingsView, self).initial_context(request)
        
        # Get item from database
        item = self.conf.provider.control_number_search(control_number)
        if item is None:
            raise Http404
        
        # Find which particular library we're interested in
        library = None
        for item_library in item.libraries:
            if item_library.location == tuple(sublocation.split('/')):
                library = item_library
        
        if library is None:
            raise Http404

        context.update({
            'item': item,
            'library': library,
            'control_number': control_number,
            'books': item.libraries[library],
        })
        return context

    def get_metadata(self, request, control_number, sublocation):
        return {
            'show_in_results': False,
        }

    @BreadcrumbFactory
    def breadcrumb(self, request, context, control_number, sublocation):
        return Breadcrumb(
            self.conf.local_name,
            lazy_parent('item-detail', control_number=control_number),
            _('Item holdings information'),
            lazy_reverse('item-holdings-detail', args=[control_number,sublocation]),
        )

    def handle_GET(self, request, context, control_number, sublocation):
        return self.render(request, context, 'library/item_holdings_detail')
