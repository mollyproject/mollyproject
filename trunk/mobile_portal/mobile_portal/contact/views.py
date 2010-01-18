import simplejson, hashlib, urllib2
from django.http import HttpResponse
from django.core.paginator import Paginator
from search import contact_search

from mobile_portal.utils.renderers import mobile_render
from mobile_portal.utils.views import BaseView
from mobile_portal.utils.breadcrumbs import *

# See http://en.wikipedia.org/wiki/Nobility_particle for more information.
NOBILITY_PARTICLES = set([
    'de', 'van der', 'te', 'von', 'van', 'du', 'di'
])

class IndexView(BaseView):
    def initial_context(cls, request):
        return {
            'method': 'phone' if request.GET.get('method')=='phone' else 'email',
            'query': request.GET.get('q', ''),
        }
        
    @BreadcrumbFactory
    def breadcrumb(cls, request, context):
        return Breadcrumb(
            'contact',
            None,
            'Contact search',
            lazy_reverse('contact_index'),
        )
        
    def handle_GET(cls, request, context):
        if request.GET and request.GET.get('q', '').strip():
    
            # Examples of initial / surname splitting
            # William Bloggs is W, Bloggs
            # Bloggs         is  , Bloggs
            # W Bloggs       is W, Bloggs
            # Bloggs W       is W, Bloggs
            # Bloggs William is B, William
            parts = request.GET.get('q', '').split(' ')
            parts = [p for p in parts if p]
            i = 0
    
            while i < len(parts)-1:
                if parts[i].lower() in NOBILITY_PARTICLES:
                    parts[i:i+2] = [' '.join(parts[i:i+2])]
                elif parts[i] == '':
                    parts[i:i+1] = []
                else:
                    i += 1
            
            parts = parts[:2]
            if len(parts) == 1:
                surname, initial = parts[0], None
            elif parts[0].endswith(','):
                surname, initial = parts[0][:-1], parts[1][:1]
            elif len(parts[1]) == 1:
                surname, initial = parts[0], parts[1]
            else:
                surname, initial = parts[1], parts[0][:1]
    
            try:
                people = contact_search(surname, initial, True, context['method'])
            except urllib2.URLError:
                return cls.handle_error(
                    request, context, 
                    'Sorry; there was a temporary issue retrieving results.' +
                    ' Please try again shortly.'
                )
                
            paginator = Paginator(people, 10)
            try:
                page = int(request.GET.get('page', '1'))
            except ValueError:
                page = 1
            if not (1 <= page <= paginator.num_pages):
                return cls.handle_error(
                    request, context,
                    'There are no results for this page.',
                )
            page = paginator.page(page) 
            
            context.update({
                'people': people,
                'page': page,
                'paginator': paginator,
            })
        else:
            context.update({
                'people': None,
            })
            
        if 'format' in request.GET and request.GET['format'] == 'json':
            json = simplejson.dumps(context)
            response = HttpResponse(
                json,
                mimetype='application/json'
            )
    #        response['X-JSON'] = json
            response['ETag'] = hashlib.sha224(json).hexdigest()
            return response
        else:
            return mobile_render(request, context, 'contact/index')
            
    def handle_error(cls, request, context, message):
        context.update({
            'message': message,
        })
                
        return mobile_render(request, context, 'contact/index')

if False:
    def quick_contacts(request):
        if request.user.is_authenticated():
            units = get_person_units(request.user.get_profile().webauth_username)
        else:
            units = [] 
        context = {
            'units': units,
        }
        return mobile_render(request, context, 'contact/quick')
