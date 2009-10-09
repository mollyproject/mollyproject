import pprint

from PyZ3950 import zoom

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
            
        if (title or author) and isbn:
            error_message = 'You cannot specify both an ISBN and a title or author.'
        else:
            error_message = None

        try:
            if not error_message and (title or author or isbn):
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
                    'error_message': error_message,
                }
        except zoom.Bib1Err, e:
            error_message = e.message
            context = {
                'search_form': search_form,
                'error_message': error_message,
            }
        except zoom.ConnectionError, e:
            context = {
                'search_form': search_form,
                'error_message': 'There was a problem contacting the library server.',
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

    libraries = item.libraries.items()
    libraries.sort(key=lambda (l,i):l.location)
    
    context = {
        'item': item,
        'libraries': libraries,
        'control_number': control_number,
    }

    return mobile_render(request, context, 'z3950/item_detail')


def item_holdings_detail(request, control_number, sublocation):
    try:
        zoom = int(request.GET['zoom'])
    except (ValueError, KeyError):
        zoom = 16
    else:
        zoom = min(max(10, zoom), 18)

    items = search.ControlNumberSearch(control_number)
    if len(items) == 0:
         raise Http404
    item = items[0]
    
    try:
        library = [l for l in item.libraries if l.location[1] == sublocation][0]
    except IndexError:
        raise Http404
        
    books = item.libraries[library]
    print library.oxpoints_entity.location
    context = {
        'item': item,
        'library': library,
        'control_number': control_number,
        'books': books,
        'zoom': zoom,
    }
    
    return mobile_render(request, context, 'z3950/item_holdings_detail')