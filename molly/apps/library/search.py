import simplejson
import re
from itertools import cycle

from django.core.urlresolvers import reverse

from molly.apps.library.models import LibrarySearchQuery

def validate_isxn(s):

    def encode(s):
        return ''.join(str(d) if d < 10 else 'X' for d in s)
    def decode(s):
        return [10 if d=='X' else int(d) for d in s]
    def isxn_checksum(s, initial=None):
        if not initial:
            initial = len(s)
        cs = 0
        for d in s:
            cs, initial = (cs + (d*initial)) % 11, initial - 1
        return cs
    def ean_checksum(s):
        return sum(d*m for d,m in zip(s, cycle([1,3]))) % 10

    s = re.sub('[*#]', 'X', s.replace('-','').strip().upper())
    if not re.match("97[789]\d{10}|\d{7}(\d{2})?[\dX]$", s):
        return None, None
    s = decode(s)

    if len(s) == 13:
        if ean_checksum(s) != 0:
            return None, None
        if s[2] == 7:
            s = s[3:10] + [(11-isxn_checksum(s[3:10], initial=8)) % 11]
            return encode(s), 'issn'
        else:
            return encode(s), 'isbn'
    else:
        cs, n = 0, len(s)
        for d in s:
            cs, n = (cs + (d*n)) % 11, n - 1
        if cs != 0:
            return None, None
        return encode(s), ('issn' if len(s) == 8 else 'isbn')

# Application Search
class ApplicationSearch(object):
    
    def __init__(self, application):
        self.conf = application
    
    def perform_search(self, request, query, only_app):
        number, number_type = validate_isxn(query)
        if not number_type:
            return []
        else:
            query = {
                number_type: number
            }
        
        query = LibrarySearchQuery(**query)
        
        results = []
        for item in self.conf.provider.library_search(query):
            results.append({
                'title': item.title,
                'redirect_if_sole_result': True,
                'application': 'library',
                'excerpt': '',
                'additional': '<strong>Library item</strong>, Publisher: %s' % item.publisher,
                'url': reverse('library:item-detail', args=[item.control_number]),
            })
        
        return results
