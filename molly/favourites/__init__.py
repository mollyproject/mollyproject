"""
Utilities to help handling favourites
"""

from django.http import Http404
from django.core.urlresolvers import resolve
from molly.favourites.models import Favourite

def get_favourites(request):
    """
    Returns a list of favourites, the list is of objects with attributes url and
    metadata
    """
    
    # Handle the old style of favourites first
    if 'favourites' in request.session:
        for url in request.session['favourites']:
            Favourite(user=request.user, url=url).save()
        del request.session['favourites']
    
    favourites = Favourite.objects.filter(user=request.user)
    urls = set()
    
    for favourite in favourites:
        if favourite.url in urls:
            favourite.delete()
        else:
            try:
                view, args, kwargs = resolve(favourite.url)
                favourite.metadata = view.get_metadata(request, *args, **kwargs)
            except Http404:
                favourite.delete()
            else:
                urls.add(favourite.url)
    
    return favourites