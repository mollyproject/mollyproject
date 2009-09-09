import simplejson, hashlib
from django.http import HttpResponse
from mobile_portal.core.renderers import mobile_render
from mobile_portal.core.ldap_queries import get_person_units
from search import contact_search


def index(request):
    if request.GET:
        method = request.GET.get('method')
        method = 'phone' if method == 'phone' else 'email'
        try:
            page = int(request.GET.get('page'))
        except:
            page = 1

        # Examples of initial / surname splitting
        # William Bloggs is W, Bloggs
        # Bloggs         is  , Bloggs
        # W Bloggs       is W, Bloggs
        # Bloggs W       is W, Bloggs
        # Bloggs William is B, William
        parts = request.GET.get('q', '').split(' ')[:2]
        if len(parts) == 1:
            surname, initial = parts[0], None
        elif len(parts[1]) == 1:
            surname, initial = parts[0], parts[1]
        else:
            surname, initial = parts[1], parts[0][:1]

        people, page_count = contact_search(surname, initial, True, method, page)

        context = {
            'people': people,
            'page': page,
            'page_count': page_count,
            'more_pages': page != page_count,
            'pages': range(1, page_count+1),
            'query': request.GET.get('q', ''),
            'method': method,
        }
    else:
        context = {
            'people': None,
            'method': 'email'
        }
        
    if 'format' in request.GET and request.GET['format'] == 'json':
        json = simplejson.dumps(context)
        response = HttpResponse(
            json,
            mimetype='application/json'
        )
        response['X-JSON'] = json
        response['ETag'] = hashlib.sha224(json).hexdigest()
        return response
    else:
        return mobile_render(request, context, 'contact/index')

def quick_contacts(request):
    if request.user.is_authenticated():
        units = get_person_units(request.user.get_profile().webauth_username)
    else:
        units = [] 
    context = {
        'units': units,
    }
    return mobile_render(request, context, 'contact/quick')