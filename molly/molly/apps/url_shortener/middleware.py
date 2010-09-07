import re

from django.http import HttpResponsePermanentRedirect

from .models import ShortenedURL

class URLShortenerMiddleware(object):
    url_re = re.compile(r"/[a-zA-Z\d]+")
    def process_response(self, request, response):
        if response.status_code == 404 and self.url_re.match(request.path):
            try:
                shortened_url = ShortenedURL.objects.get(slug=request.path[1:])
                return HttpResponsePermanentRedirect(shortened_url.path)
            except:
                pass
        return response
