"""
Utilities to help handling favourites
"""

from django.http import Http404
from django.core.urlresolvers import resolve
from django.dispatch import receiver

from molly.auth import unifying_users
from molly.favourites.models import Favourite

@receiver(unifying_users)
def unify_users(sender, users, into, **kwargs):
    # Update favourites when merging users
    Favourite.objects.filter(user__in=users).update(user=into)

def get_favourites(request):
    """
    Returns a list of favourites, the list is of objects with attributes url and
    metadata
    """
    
    # If the user is anonymous, use sessions, otherwise associate it with the
    # user
    if request.user.is_anonymous():
        favourites = [Favourite(url=url) for url in request.session.get('favourites', [])]
    
    else:
        
        # Handle the old style of favourites first
        if 'favourites' in request.session:
            for url in request.session['favourites']:
                Favourite(user=request.user, url=url).save()
            del request.session['favourites']
        
        favourites = Favourite.objects.filter(user=request.user)
    
    # Dedupe and annotate with metadata
    urls = set()
    for favourite in favourites:
        if favourite.url in urls:
            if not request.user.is_anonymous():
                favourite.delete()
            else:
                request.session['favourites'].remove(favourite.url)
        else:
            try:
                view, args, kwargs = resolve(favourite.url)
                favourite.metadata = view.get_metadata(request, *args, **kwargs)
            except Http404:
                if not request.user.is_anonymous():
                    favourite.delete()
                else:
                    request.session['favourites'].remove(favourite.url)
            else:
                urls.add(favourite.url)
        
    return favourites
