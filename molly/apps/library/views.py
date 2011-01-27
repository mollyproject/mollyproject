from django.core.paginator import Paginator

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
        
        # Call providers
        results = []
        for provider in reversed(self.conf.providers):
            results.append(provider.library_search(query))
        
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
    
    def initial_context(cls, request, control_number):
        items = search.ControlNumberSearch(control_number, cls.conf)
        if len(items) == 0:
                raise Http404

        display_map = {
            'true':True, 'false':False
        }.get(request.GET.get('with_map'))
        if display_map is None:
            display_map = (not request.session.get('geolocation:location') is None)

        return {
            'zoom': cls.get_zoom(request, None),
            'item': items[0],
            'control_number': control_number,
            'display_map': display_map,
            'complex_shorten': True,
        }

    @BreadcrumbFactory
    def breadcrumb(cls, request, context, control_number):
        return Breadcrumb(
            cls.conf.local_name,
            lazy_parent('search'),
            'Search result',
            lazy_reverse('item-detail', args=[control_number]),
        )

    def handle_GET(cls, request, context, control_number):
        return (cls.handle_with_location if context['display_map'] else cls.handle_without_location)(request, context)

    def handle_with_location(cls, request, context):
        points = []
        location = request.session.get('geolocation:location')

        all_libraries = context['item'].libraries.items()
        libraries, stacks = [], []
        for library, items in all_libraries:
            if library.oxpoints_id and library.oxpoints_entity.is_stack:
                stacks.append( (library, items) )
            else:
                libraries.append( (library, items) )

        if libraries:
            entity_ids = set(l.oxpoints_id for l in context['item'].libraries if l.oxpoints_id)
            entities = Entity.objects.filter(_identifiers__scheme='oxpoints', _identifiers__value__in = entity_ids)
            if location:
                point = Point(location[1], location[0], srid=4326)

                with_location = entities.filter(location__isnull=False)
                without_location = entities.filter(location__isnull=True)

                if with_location.count() == 0:
                    return cls.handle_without_location(request, context)

                entities = chain(
                    with_location.distance(point).order_by('distance'),
                    without_location.order_by('title'),
                )

                ordering = dict((e.identifiers['oxpoints'], i) for i, e in enumerate(entities))

                libraries.sort(key=lambda l:(ordering[l[0].oxpoints_id] if l[0].oxpoints_id else float('inf')))

            else:
                entities.order_by('title')

            for library, books in libraries:
                if not (library.oxpoints_id and library.oxpoints_entity.location):
                    library.has_location = False
                    continue
                color = AVAIL_COLORS[max(b['availability'] for b in books)]
                points.append( (
                    library.oxpoints_entity.location[0],
                    library.oxpoints_entity.location[1],
                    color,
                    library.oxpoints_entity.title,
                ) )

            map = Map(
                centre_point = (location[0], location[1], 'green', '') if location else None,
                points = points,
                min_points = 0 if context['zoom'] else len(points),
                zoom = context['zoom'],
                width = request.map_width,
                height = request.map_height,
            )

            # Yes, this is weird. fit_to_map() groups libraries with the same location
            # so here we add a marker_number to each library to display in the
            # template.
            lib_iter = iter(libraries)
            for i, (a,b) in enumerate(map.points):
                for j in range(len(b)):
                    lib_iter.next()[0].marker_number = i + 1
            # Finish off by adding a marker_number for those that aren't on the map.
            # (lib_iter still contains the remaining items after the above calls to
            # next() ).
            for library in lib_iter:
                library[0].marker_number = None
        
        context.update({
            'libraries': libraries,
            'stacks': stacks,
            'map': map,
        })

        return cls.render(request, context, 'z3950/item_detail')

    def handle_without_location(cls, request, context):
        libraries = context['item'].libraries.items()
        libraries.sort(key=lambda (l,i):l.location)

        context['libraries'] = libraries

        return cls.render(request, context, 'z3950/item_detail')

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
