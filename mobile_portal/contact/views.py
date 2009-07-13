from mobile_portal.core.renderers import mobile_render
from search import contact_search

def index(request):
    if request.GET:
        method = request.GET.get('method', '')
        method = 'phone' if method == 'phone' else 'email'
        try:
            page = int(request.GET.get('page'))
        except:
            page = 1

        parts = request.GET.get('q', '').split(' ')[:2]
        if len(parts) == 1:
            surname, initial = parts[0], None
        elif len(parts[0]) > len(parts[1]):
            surname, initial = parts[0], parts[1][:1]
        else:
            surname, initial = parts[1], parts[0][:1]

        people, page_count = contact_search(surname, initial, True, method, page)

        context = {
            'people': people,
            'page_count': page_count,
            'pages': range(1, page_count+1),
            'query': request.GET.get('q', ''),
            'method': method,
        }
    else:
        context = {
            'people': None,
            'method': 'email'
        }
        
    return mobile_render(request, context, 'contact/index')
