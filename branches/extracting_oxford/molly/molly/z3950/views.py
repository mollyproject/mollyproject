from itertools import chain
from PyZ3950 import zoom
import logging

from django.http import Http404, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator
from django.contrib.gis.geos import Point

from molly.utils.views import BaseView
from molly.utils.breadcrumbs import *
from molly.utils.renderers import mobile_render

from molly.maps.models import Entity
from molly.osm.utils import fit_to_map

from . import search
from .forms import SearchForm

STOP_WORDS = frozenset( (
    "a,able,about,across,after,all,almost,also,am,among,an,and,any,are,as,at,"
  + "be,because,been,but,by,can,cannot,could,dear,did,do,does,either,else,"
  + "ever,every,for,from,get,got,had,has,have,he,her,hers,him,his,how,however,"
  + "i,if,in,into,is,it,its,just,least,let,like,likely,may,me,might,most,must,"
  + "my,neither,no,nor,not,of,off,often,on,only,or,other,our,own,rather,said,"
  + "say,says,she,should,since,so,some,than,that,the,their,them,then,there,"
  + "these,they,this,tis,to,too,twas,us,wants,was,we,were,what,when,where,"
  + "which,while,who,whom,why,will,with,would,yet,you,your" ).split(',') )

search_logger = logging.getLogger('molly.z3950.searches')
logger = logging.getLogger('molly.z3950')

class IndexView(BaseView):
    def get_metadata(cls, request):
        return {
            'title': 'Library search',
            'additional': "View libraries' contact information and find library items.",
        } 

    def initial_context(cls, request):
        return {
            'search_form': SearchForm()
        }
        
    @BreadcrumbFactory
    def breadcrumb(cls, request, context):
        return Breadcrumb(cls.conf.local_name, None, 'Library search', lazy_reverse('z3950:index'))
        
    def handle_GET(cls, request, context):
        return mobile_render(request, context, 'z3950/index')

class SearchDetailView(BaseView):
    def get_metadata(cls, request):
        return {
            'show_in_results': False,
        }
        
    def initial_context(cls, request):
        return {
            'search_form': SearchForm(request.GET),
        }
    
    @BreadcrumbFactory
    def breadcrumb(cls, request, context):
        x = 'item' in context or context['search_form'].is_valid()
        return Breadcrumb(
            cls.conf.local_name,
            lazy_parent(IndexView),
            'Search results' if x else 'Library search',
            lazy_reverse('z3950:search'),
        )
        
    class InconsistentQuery(ValueError):
        def __init__(self, msg):
            self.msg = msg
        
    def clean_input(cls, s):
        s = s.replace('"', '').lower()
        removed = frozenset(w for w in s.split(' ') if (w in STOP_WORDS))
        s = ' '.join(w for w in s.split(' ') if (not w in STOP_WORDS))
        return s, removed

    def clean_isbn(cls, s):
        s = s.replace('*', 'X')
        s = ''.join(c for c in s if (c in '0123456789X'))
        return s
                        
    def handle_GET(cls, request, context):
        search_form = context['search_form']
        
        if not (request.GET and search_form.is_valid()):
            return cls.handle_no_search(request, context)

        try:
            query, removed = cls.construct_query(request, search_form)
        except cls.InconsistentQuery, e:
            return cls.handle_error(request, context, e.msg)

        try:
            results = search.OLISSearch(query, provider=cls.conf.provider)
        except Exception, e:
            logger.exception("Library query error")
            return cls.handle_error(request, context, 'An error occurred: %s' % e)
    
        paginator = Paginator(results, 10)
    
        try:
            page_index = int(request.GET['page'])
        except (ValueError, KeyError):
            page_index = 1
        else:
            page_index = min(max(1, page_index), paginator.num_pages)
        
        page = paginator.page(page_index)

        context.update({
            'removed': removed,
            'paginator': paginator,
            'page': page,
        })
        return mobile_render(request, context, 'z3950/item_list')
    
    def handle_no_search(cls, request, context):
        return mobile_render(request, context, 'z3950/item_list')
        
    def handle_error(cls, request, context, message):
        context['error_message'] = message
        return mobile_render(request, context, 'z3950/item_list')
        
    def construct_query(cls, request, search_form):
        query, removed = [], set()
        title, author, isbn = '', '', ''
        if search_form.cleaned_data['author']:
            author, new_removed = cls.clean_input(search_form.cleaned_data['author'])
            removed |= new_removed
            query.append('(au="%s")' % author)
        if search_form.cleaned_data['title']:
            title, new_removed = cls.clean_input(search_form.cleaned_data['title'])
            removed |= new_removed
            query.append('(ti="%s")' % title)
        if search_form.cleaned_data['isbn']:
            isbn = cls.clean_isbn(search_form.cleaned_data['isbn'])
            query.append('(isbn=%s)' % isbn)
            
        if (title or author) and isbn:
            raise cls.InconsistentQuery("You cannot specify both an ISBN and a title or author.")
            
        if not (title or author or isbn):
            raise cls.InconsistentQuery("You must supply some subset of title or author, and ISBN.")

        search_logger.info("Library query", extra={
            'session_key': request.session.session_key,
            'title': title,
            'author': author,
            'isbn': isbn,
        })        
        
        return "and".join(query), removed


AVAIL_COLORS = ['red', 'amber', 'purple', 'blue', 'green']

class ItemDetailView(BaseView):
    def initial_context(cls, request, control_number):
        items = search.ControlNumberSearch(control_number, cls.conf.provider)
        if len(items) == 0:
                raise Http404

        display_map = {
            'true':True, 'false':False
        }.get(request.GET.get('with_map'))
        if display_map is None:
            display_map = False and (not request.session['geolocation:location'] is None)
        
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
            lazy_parent(SearchDetailView),
            'Search result',
            lazy_reverse('z3950:item_detail', args=[control_number]),
        )
               
    def handle_GET(cls, request, context, control_number):
        return (cls.handle_with_location if context['display_map'] else cls.handle_without_location)(request, context)

    def handle_with_location(cls, request, context):
        points = []
        location = request.session['geolocation:location']
    
        all_libraries = context['item'].libraries.items()
        libraries, stacks = [], []
        for library, items in all_libraries:
            if library.oxpoints_id and library.oxpoints_entity.is_stack:
                stacks.append( (library, items) )
            else:
                libraries.append( (library, items) )
    
        if libraries:
            entity_ids = set(l.oxpoints_id for l in context['item'].libraries if l.oxpoints_id)
            entities = Entity.objects.filter(oxpoints_id__in = entity_ids)
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
        
                ordering = dict((e.oxpoints_id, i) for i, e in enumerate(entities))
        
                libraries.sort(key=lambda l:(ordering[l[0].oxpoints_id] if l[0].oxpoints_id else float('inf')))
        
            else:
                entities.order_by('title')
        
            for library, books in libraries:
                if not (library.oxpoints_id and library.oxpoints_entity.location):
                    library.has_location = False
                    continue
                color = AVAIL_COLORS[max(b['availability'] for b in books)]
                points.append( (
                    library.oxpoints_entity.location[1],
                    library.oxpoints_entity.location[0],
                    color,
                ) )
                
        
            map_hash, (new_points, zoom) = fit_to_map(
                centre_point = (location[0], location[1], 'green') if location else None,
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
            for i, (a,b) in enumerate(new_points):
                for j in range(len(b)):
                    lib_iter.next()[0].marker_number = i + 1
            # Finish off by adding a marker_number for those that aren't on the map.
            # (lib_iter still contains the remaining items after the above calls to
            # next() ).
            for library in lib_iter:
                library[0].marker_number = None
                
            context['zoom'] = zoom
            context['map_hash'] = map_hash
    
        context.update({
            'libraries': libraries,
            'stacks': stacks
        })
        
        return mobile_render(request, context, 'z3950/item_detail')



        
    def handle_without_location(cls, request, context):
        libraries = context['item'].libraries.items()
        libraries.sort(key=lambda (l,i):l.location)
        
        context['libraries'] = libraries
        
        return mobile_render(request, context, 'z3950/item_detail')

class ItemHoldingsView(BaseView):
    def initial_context(cls, request, control_number, sublocation):
        items = search.ControlNumberSearch(control_number)
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
            lazy_parent(ItemDetailView, control_number=control_number),
            'Item holdings information',
            lazy_reverse('z3950:item_holdings_detail', args=[control_number,sublocation]),
        )

    def handle_GET(cls, request, context, control_number, sublocation):
        return mobile_render(request, context, 'z3950/item_holdings_detail')
