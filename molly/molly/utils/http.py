import urlparse, urllib

from django.http import HttpResponseRedirect


# parse_qs was copied from cgi to urlparse in Python 2.6
# We'll copy it outselves if it's not already there.
if not hasattr(urlparse, 'parse_qs'):
    import cgi
    urlparse.parse_qs = cgi.parse_qs
    del cgi


class HttpResponseSeeOther(HttpResponseRedirect):
    status_code = 303

def update_url(url, query_update, fragment = ''):
    """
    Replaces query parameters with those given in query_update, and updates the fragment.
    
    Use None to remove the relevant bits of the URL.
    """
    
    url = urlparse.urlparse(url)
    query = urlparse.parse_qs(url.query)
    for key, value in query_update.items():
        if value is None:
            query.pop(key, None)
        else:
            query[key] = value
    fragment = url[5] if fragment == '' else fragment
    return urlparse.urlunparse(url[:4] + (urllib.urlencode(query), fragment))
                