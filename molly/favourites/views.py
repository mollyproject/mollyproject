from django.http import Http404
from django.core.urlresolvers import resolve

from molly.utils.views import BaseView
from molly.utils.breadcrumbs import lazy_reverse, Breadcrumb, BreadcrumbFactory

from molly.favourites import get_favourites
from molly.favourites.models import Favourite

class FavouritableView(BaseView):
    """
    A view to inherit from if you want to be favouritable
    """
    
    def initial_context(self, request, *args, **kwargs):
        
        context = super(FavouritableView, self).initial_context(request, *args, **kwargs)
        
        # Add whether or not this is favouritable to the context
        context['is_favouritable'] = True
        
        # Also, add whether or not this particular thing already is favourited
        context['is_favourite'] = request.path_info in [f.url for f in get_favourites(request)]
        
        # And the URL of this page (so it can be favourited)
        context['favourite_url'] = request.path_info
        
        return context

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
        context['favourites'] = get_favourites(request)
        return self.render(request, context, 'favourites/index')
    
    def handle_POST(self, request, context):
        """
        Add and remove favourites. Favourites are stored as URLs (the part of
        them Django is interested in anyway) in the database, if the user is
        logged in - otherwise, it is stored in the session, and then migrated
        to the database when the user logs in. This has the downside of breaking
        favourites if URLs change.
        """
        
        # Alter favourites list
        if 'URL' in request.POST:
            
            if 'favourite' in request.POST:
                # Add
                try:
                    resolve(request.POST['URL'])
                except Http404:
                    # This means that they tried to save a URL that doesn't exist
                    # or isn't on our site
                    return self.redirect(lazy_reverse('favourites:index'), request)
                else:
                    if request.user.is_anonymous():
                        if 'favourites' not in request.session:
                            request.session['favourites'] = set()
                        request.session['favourites'].add(request.POST['URL'])
                        request.session.modified = True
                    else:
                        if request.user.is_anonymous():
                            if request.POST['URL'] in request.session.get('favourites', set()):
                                request.session['favourites'].remove(request.POST['URL'])
                                request.session.modified = True
                        else:
                            Favourite(user=request.user, url=request.POST['URL']).save()
            
            elif 'unfavourite' in request.POST:
                if not request.user.is_anonymous():
                    try:
                        favourite = Favourite.objects.get(user=request.user,
                                                          url = request.POST['URL'])
                    except Favourite.DoesNotExist:
                        pass
                    else:
                        favourite.delete()
                else:
                    if request.POST['URL'] in request.session.get('favourites', set()):
                        request.session['favourites'].remove(request.POST['URL'])
                        request.session.modified = True
        
            # If the source was the favourites page, redirect back there
            if 'return_to_favourites' in request.POST:
                return self.handle_GET(request, context)
            
            # else the source
            else:
                return self.redirect(request.POST['URL'], request)
            
        else:
            # Missing POST data, probably a bad request
            return self.redirect(lazy_reverse('favourites:index'), request)
