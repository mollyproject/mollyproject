"""
Utilities to help handling favourites
"""

from django.http import Http404

from django.core.urlresolvers import resolve

def get_favourites(request):
    """
    Returns a list of favourites, the list is tuples of (title, URL)
    """
    
    fs = []
    for url in (request.session['favourites'] if 'favourites' in request.session else []):
        # Remove broken links from the favourites
        try:
            view, args, kwargs = resolve(url)
            breadcrumb = view.breadcrumb(request, view.initial_context(request, *args, **kwargs), *args, **kwargs)
            fs.append((breadcrumb[4], url))
        except Http404:
            request.session['favourites'].remove(url)
            request.session.modified = True
    
    return fs