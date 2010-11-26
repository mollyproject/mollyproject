"""
Utilities to help handling favourites
"""

from django.http import Http404

from django.core.urlresolvers import resolve

def get_favourites(request):
    """
    Returns a list of favourites, the list is of dictionaries with keys URL and metadata
    """
    
    fs = []
    for url in (request.session['favourites'] if 'favourites' in request.session else []):
        # Remove broken links from the favourites
        try:
            view, args, kwargs = resolve(url)
            fs.append({'url': url, 'metadata': view.get_metadata(request, *args, **kwargs)})
        except Http404:
            request.session['favourites'].remove(url)
            request.session.modified = True
    
    return fs