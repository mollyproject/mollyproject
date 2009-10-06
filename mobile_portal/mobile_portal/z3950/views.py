
from django.http import Http404, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator
from django.contrib.gis.geos import Point

from mobile_portal.core.renderers import mobile_render
from mobile_portal.z3950 import search
from mobile_portal.z3950.forms import SearchForm

from mobile_portal.oxpoints.models import Entity
from mobile_portal.osm.utils import fit_to_map

STOP_WORDS = frozenset( (
    "a,able,about,across,after,all,almost,also,am,among,an,and,any,are,as,at,"
  + "be,because,been,but,by,can,cannot,could,dear,did,do,does,either,else,"
  + "ever,every,for,from,get,got,had,has,have,he,her,hers,him,his,how,however,"
  + "i,if,in,into,is,it,its,just,least,let,like,likely,may,me,might,most,must,"
  + "my,neither,no,nor,not,of,off,often,on,only,or,other,our,own,rather,said,"
  + "say,says,she,should,since,so,some,than,that,the,their,them,then,there,"
  + "these,they,this,tis,to,too,twas,us,wants,was,we,were,what,when,where,"
  + "which,while,who,whom,why,will,with,would,yet,you,your" ).split(',') )

def index(request):
    search_form = SearchForm()
    context = {
        'search_form': search_form
    }
    return mobile_render(request, context, 'z3950/index')

def search_detail(request):
    def clean_input(s):
        s = s.replace('"', '').lower()
        removed = frozenset(w for w in s.split(' ') if (w in STOP_WORDS))
        print "R", frozenset(w for w in s.split(' ') )
        s = ' '.join(w for w in s.split(' ') if (not w in STOP_WORDS))
        return s, removed
    def clean_isbn(s):
        s = s.replace('*', 'X')
        s = ''.join(c for c in s if (c in '0123456789X'))
        return s
        
    search_form = SearchForm(request.GET)
    
    if search_form.is_valid():
        query, removed = [], set()
        title, author, isbn = '', '', ''
        if search_form.cleaned_data['author']:
            author, new_removed = clean_input(search_form.cleaned_data['author'])
            removed |= new_removed
            query.append('(au="%s")' % author)
        if search_form.cleaned_data['title']:
            title, new_removed = clean_input(search_form.cleaned_data['title'])
            removed |= new_removed
            query.append('(ti="%s")' % title)
        if search_form.cleaned_data['isbn']:
            isbn = clean_isbn(search_form.cleaned_data['isbn'])
            query.append('(isbn=%s)' % isbn)

        if query:
            query = "and".join(query)
            results = search.OLISSearch(query)

            paginator = Paginator(results, 10)
        
            try:
                page_index = int(request.GET['page'])
            except (ValueError, KeyError):
                page_index = 1
            else:
                page_index = min(max(1, page_index), paginator.num_pages)
            
            page = paginator.page(page_index)
    
            context = {
                'search_form': search_form,
                'removed': removed,
                'paginator': paginator,
                'page': page,
                'title': title,
                'author': author,
                'isbn': isbn,
            }

        else:
            context = {
                'search_form': search_form,
            }

    else:
        context = {
            'search_form': search_form,
        }

    return mobile_render(request, context, 'z3950/item_list')


AVAIL_COLORS = ['red', 'amber', 'purple', 'blue', 'green']
def item_detail(request, control_number):

    try:
        zoom = int(request.GET['zoom'])
    except (ValueError, KeyError):
        zoom = None
    else:
        zoom = min(max(10, zoom), 18)

    items = search.ControlNumberSearch(control_number)
    if len(items) == 0:
            raise Http404

    item = items[0]

    location = request.preferences['location']['location']

    points = []

    all_libraries = item.libraries.items()
    libraries, stacks = [], []
    for library, items in all_libraries:
        if library.oxpoints_id and library.oxpoints_entity.is_stack:
            stacks.append( (library, items) )
        else:
            libraries.append( (library, items) )
            
    print libraries

    if libraries:
        entity_ids = set(l.oxpoints_id for l in item.libraries if l.oxpoints_id)
        entities = Entity.objects.filter(oxpoints_id__in = entity_ids)
        if location:
            point = Point(location[1], location[0], srid=4326)
            entities = entities.distance(point).order_by('distance')
    
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
            min_points = 0 if zoom else len(points),
            zoom = zoom,
            width = request.device.max_image_width,
            height = request.device.max_image_height,
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

    context = {
        'item': item,
        'libraries': [],
        'map_hash': None,
        'zoom': zoom,
        'stacks': stacks
    }
    
    if libraries:
        context.update({
            'libraries': libraries,
            'map_hash': map_hash,
            'zoom': zoom,
        })
#        
    return mobile_render(request, context, 'z3950/item_detail')
