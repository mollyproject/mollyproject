from django.http import HttpResponseRedirect, Http404
from django.core.urlresolvers import resolve

from molly.utils.views import BaseView
from molly.utils.breadcrumbs import lazy_reverse, Breadcrumb, BreadcrumbFactory

class FavouritableView(BaseView):
    """
    A view to inherit from if you want to be favouritable
    """
    
    def initial_context(self, request, *args, **kwargs):
        
        context = super(FavouritableView, self).initial_context(request, *args, **kwargs)
        
        # Add whether or not this is favouritable to the context
        context['is_favouritable'] = True
        
        # Also, add whether or not this particular thing already is favourited
        context['is_favourite'] = request.path_info in (request.session['favourites'] if 'favourites' in request.session else [])
        print request.session['favourites']
        print request.path_info
        print context['is_favourite']
        
        # And the URL of this page (so it can be favourited)
        context['favourite_url'] = request.path_info
        
        return context
    
    def get_related(self, request, context, *args, **kwargs):
        """
        This allows a view to be queried for any related objects (such as an
        entity it represents). This allows for things like favouriting places to
        also get at the particular entity that is favourited.
        """
        
        # By default return an empty list
        return []

class IndexView(BaseView):
    """
    Allows for favourites management
    """
    
    @BreadcrumbFactory
    def breadcrumb(self, request, context):
        return Breadcrumb(
            self.conf.local_name,
            None,
            'Favourites',
            lazy_reverse('index'),
        )
    
    def handle_GET(self, request, context):
        """
        Show a list of favourited things, and allow removal of these
        """
        context['favourites'] = request.session['favourites'] if 'favourites' in request.session else []
        return self.render(request, context, 'favourites/index')
    
    def handle_POST(self, request, context):
        """
        Add and remove favourites. Favourites are stored as URLs (the part of
        them Django is interested in anyway) in the database. This has the
        downside of breaking favourites if URLs change.
        """
        
        # Alter favourites list
        if 'URL' in request.POST:
            
            if 'favourites' not in request.session:
                request.session['favourites'] = set()
            
            if 'favourite' in request.POST:
                # Add
                try:
                    resolve(request.POST['URL'])
                    request.session['favourites'].add(request.POST['URL'])
                    request.session.modified = True
                except Http404:
                    # This means that they tried to save a URL that doesn't exist
                    # or isn't on our site
                    return HttpResponseRedirect(lazy_reverse('favourites:index'))
            
            elif 'unfavourite' in request.POST and 'favourites' in request.session:
                # Remove
                if request.POST['URL'] in request.session['favourites']:
                    request.session['favourites'].remove(request.POST['URL'])
                    request.session.modified = True
        
            # If the source was the favourites page, redirect back there
            if 'return_to_favourites' in request.POST:
                return self.handle_GET(request, context)
            
            # else the source
            else:
                return HttpResponseRedirect(request.POST['URL'])
            
        else:
            # Missing POST data, probably a bad request
            return HttpResponseRedirect(lazy_reverse('favourites:index'))