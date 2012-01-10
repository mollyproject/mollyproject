import random
import re

from molly.url_shortener.models import ShortenedURL

# We'll omit characters that look similar to one another
AVAILABLE_CHARS = '23456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghkmnpqrstuvwxyz'
has_alpha_re = re.compile(r'[a-zA-Z]')

def get_shortened_url(path, request, complex_shorten=False):
    """
    Given a path (as returned by, for example, reverse), then return a fully
    qualified short URL for that path. Also needs the request object. An
    optional third argument, complex_shorten, will, if set to True, result in
    a more complex, but non-sequential, short URL.
    """
    
    shortened_url, created = ShortenedURL.objects.get_or_create(path=path)
    
    if created:
        if complex_shorten:
            slug = None
            while not (slug \
                       and ShortenedURL.objects.filter(slug=slug).count() == 0 \
                       and has_alpha_re.search(slug)):
                slug = ''.join(random.choice(AVAILABLE_CHARS) for i in range(5))
        else:
            slug = unicode(shortened_url.id)
        shortened_url.slug = slug
        shortened_url.save()
    
    return request.build_absolute_uri('/' + shortened_url.slug)
