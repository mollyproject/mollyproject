import re

from django.http import HttpResponseRedirect

class HttpResponseSeeOther(HttpResponseRedirect):
    status_code = 303

class MediaType(object):
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
        return not (self > other or self < other)
    
    def __cmp__(self, other):
        if self > other:
            return 1
        elif self < other:
            return -1
        else:
            return 0

    def __repr__(self):
        return "%s(%r, [%f])" % (type(self).__name__, self.value, self.priority)
    
    def provides(self, imt):
        return self.type[:imt.specifity] == imt.type[:imt.specifity]
        
    @classmethod
    def resolve(cls, accept, provide):
        accept.sort()
        groups, accept = [[accept[-1]]], accept[:-1]
        
        while accept:
            imt = accept.pop()
            if imt.equivalent(groups[0][-1]):
                groups[-1].append(imt)
            else:
                groups.append([imt])

        for imts in groups:
            for provide_type, renderer in provide:
                for imt in imts:
                    if provide_type.provides(imt):
                        return renderer
        
        raise ValueError
