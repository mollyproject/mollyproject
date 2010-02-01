import simplejson, hashlib, urllib2
from django.http import HttpResponse
from django.core.paginator import Paginator
from search import contact_search

from mobile_portal.utils.renderers import mobile_render
from mobile_portal.utils.views import BaseView
from mobile_portal.utils.breadcrumbs import *

contact_connector = settings.CONNECTORS['mobile_portal.contact']

class IndexView(BaseView):
    def initial_context(cls, request):
        return {
            'form': contact_connector.search_form(request.POST or None),
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
        if context['form'].is_valid():
    
            try:
                people = contact_connector.search(
                    request.session.sessionkey,
                    form.cleaned_data)
            except ContactConnectorException, e
                return cls.handle_error(
                    request, context, e.msg
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
