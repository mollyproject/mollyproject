import urlparse
import urllib
import re

from django.http import HttpResponseRedirect

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
                
class MediaType(object):
    """
    Represents a parsed internet media type.
    """

    _MEDIA_TYPE_RE = re.compile(r'(\*/\*)|(?P<type>[^/]+)/(\*|((?P<subsubtype>[^+]+)\+)?(?P<subtype>.+))')    
    def __init__(self, value, priority=0):
        value = unicode(value).strip()
        media_type = value.split(';')
        media_type, params = media_type[0].strip(), dict((i.strip() for i in p.split('=', 1)) for p in media_type[1:] if '=' in p)

        mt = self._MEDIA_TYPE_RE.match(media_type)
        if not mt:
            raise ValueError("Not a correctly formatted internet media type (%r)" % media_type)
        mt = mt.groupdict()

        try:
            self.quality = float(params.pop('q', 1))
        except ValueError:
            self.quality = 1

        self.type = mt.get('type'), mt.get('subtype'), mt.get('subsubtype')
        self.specifity = len([t for t in self.type if t])
        self.params = params
        self.value = value
        self.priority = priority

    def __unicode__(self):
        return self.value

    def __gt__(self, other):
        if self.quality != other.quality:
            return self.quality > other.quality
        
        if self.specifity != other.specifity:
            return self.specifity > other.specifity
        
        for key in other.params:
            if self.params.get(key) != other.params[key]:
                return False
        
        return len(self.params) > len(other.params)
    
    def __lt__(self, other):
        return other > self

    def __eq__(self, other):
        return self.quality == other.quality and self.type == other.type and self.params == other.params
    def __ne__(self, other):
        return not self.__eq__(other)
    def equivalent(self, other):
        """
        Returns whether two MediaTypes have the same overall specifity.
        """
        return not (self > other or self < other)

    def __cmp__(self, other):
        if self > other:
            return 1
        elif self < other:
            return -1
        else:
            return 0

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.value)

    def provides(self, imt):
        """
        Returns True iff the self is at least as specific as other.

        Examples:
        application/xhtml+xml provides application/xml, application/*, */*
        text/html provides text/*, but not application/xhtml+xml or application/html
        """
        return self.type[:imt.specifity] == imt.type[:imt.specifity]
        
    @classmethod
    def resolve(self, accept, provide):
        """
        Resolves a list of accepted MediaTypes and available renderers to the preferred renderer.

        Call as MediaType.resolve([MediaType], [(MediaType, renderer)]).
        """
        if len(accept) == 0:
            return []
        accept.sort()
        eq_classes, accept = [[accept[-1]]], accept[:-1]

        # Group the accepted types into equivalence classes
        while accept:
            imt = accept.pop()
            if imt.equivalent(eq_classes[0][-1]):
                eq_classes[-1].append(imt)
            else:
                eq_classes.append([imt])

        renderers, seen_renderers = [], set()

        # For each equivalence class, find the first renderer MediaType that
        # can handle one of its members, and return the renderer.
        for imts in eq_classes:
            for provide_type, renderer in provide:
                for imt in imts:
                    if renderer not in seen_renderers and provide_type.provides(imt):
                        renderers.append(renderer)
                        seen_renderers.add(renderer)

        return renderers
