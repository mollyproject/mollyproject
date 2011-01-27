import re, urllib, simplejson, traceback
from datetime import datetime
from itertools import cycle

from PyZ3950.zmarc import MARC, MARC8_to_Unicode

from django.conf import settings
from django.core.urlresolvers import reverse

from molly.apps.places.models import Entity

ITEM_RE = re.compile(r'(?P<heading>\d{1,3}) (..(\$(?P<sub>.)(?P<entry>[^\$]+) )+|(?P<raw>[^\$]+))')

AVAIL_UNAVAILABLE, AVAIL_AVAILABLE, AVAIL_REFERENCE, AVAIL_UNKNOWN, AVAIL_STACK = range(5)
# red, green, blue, orange, purple

AVAIL_UNAVAILABLE, AVAIL_UNKNOWN, AVAIL_STACK, AVAIL_REFERENCE, AVAIL_AVAILABLE = range(5)
# red, amber, purple, blue, green

AVAILABILITIES = {
    'Available': AVAIL_AVAILABLE,
    'Reference': AVAIL_REFERENCE,
    'Confined': AVAIL_REFERENCE,
    'Check shelf': AVAIL_UNKNOWN,
    'Please check shelf': AVAIL_UNKNOWN,
    'In place': AVAIL_STACK,
    'Missing': AVAIL_UNAVAILABLE,
    'Temporarily missing': AVAIL_UNAVAILABLE,
    'Reported Missing': AVAIL_UNAVAILABLE,
    'Withdrawn': AVAIL_UNAVAILABLE,
    '': AVAIL_UNKNOWN,
}
def require_json(f):
    def g(self, *args, **kwargs):
        try:
            if not hasattr(self, '_json'):
                self._json = simplejson.load(urllib.urlopen(
                    Library.LIBRARY_URL % self.location[-1].replace(' ', '%20')
                ))[0]
        except Exception, e:
            self._json = None
        return f(self, *args, **kwargs)
    return g

class Library(object):
    LIBRARY_URL = "http://oxpoints.oucs.ox.ac.uk/olis:%s.json"
    def __init__(self, location):
        self.location = tuple(location)

    @property
    def oxpoints_id(self):
        def f(self):
            return self._json['uri'][-8:]

        try:
            return require_json(f)(self)
        except:
            return None

    @property
    @require_json
    def oxpoints_entity(self):
        try:
            return self._oxpoints_entity
        except AttributeError:
            self._oxpoints_entity = Entity.objects.get(_identifiers__scheme='oxpoints', _identifiers__value = self.oxpoints_id)
            return self._oxpoints_entity

    @property
    @require_json
    def oxpoints_location(self):
        return self.oxpoints_entity.location

    @require_json
    def __unicode__(self):
        if self.oxpoints_id:
            return "%s (%s)" % (self.oxpoints_entity.title, self.oxpoints_id)
        else:
            return " - ".join(self.location)
    __repr__ = __unicode__

    def __hash__(self):
        return hash((type(self), self.location))

    def __eq__(self, other):
        return self.location == other.location

    def availability_display(self):
        return [
            'unavailable', 'unknown', 'stack', 'reference', 'available'
        ][self.availability]

class OLISResult(object):
    USM_CONTROL_NUMBER = 1
    USM_ISBN = 20
    USM_ISSN = 22
    USM_AUTHOR = 100
    USM_TITLE_STATEMENT = 245
    USM_EDITION = 250
    USM_PUBLICATION = 260
    USM_PHYSICAL_DESCRIPTION = 300
    USM_LOCATION = 852

    def __init__(self, result):
        self.str = str(result)
        self.metadata = {OLISResult.USM_LOCATION: []}

        items = self.str.split('\n')[1:]
        for item in items:
            heading, data = item.split(' ', 1)
            heading = int(heading)
            if heading == OLISResult.USM_CONTROL_NUMBER:
                # We strip the 'UkOxUb' from the front.
                self.control_number = data[6:]

            # We'll use a slice as data may not contain that many characters.
            # LCN 12110145 is an example where this would otherwise fail.
            if data[2:3] != '$':
                continue

            subfields = data[3:].split(' $')
            subfields = [(s[0], s[1:]) for s in subfields]

            if not heading in self.metadata:
                self.metadata[heading] = []

            m = {}
            for subfield_id, content in subfields:
                if not subfield_id in m:
                    m[subfield_id] = []
                m[subfield_id].append(content)
            self.metadata[heading].append(m)

        self.metadata = marc_to_unicode(self.metadata)

        self.libraries = {}

        for datum in self.metadata[OLISResult.USM_LOCATION]:
            library = Library(datum['b'])
            if not 'p' in datum:
                availability = AVAIL_UNKNOWN
                datum['y'] = ['Check web OPAC']
                due_date = None
            elif not 'y' in datum:
                due_date, availability = None, AVAIL_UNKNOWN
            elif datum['y'][0].startswith('DUE BACK: '):
                due_date = datetime.strptime(datum['y'][0][10:], '%d/%m/%y')
                availability = AVAIL_UNAVAILABLE
            else:
                due_date = None
                availability = AVAILABILITIES.get(datum['y'][0], AVAIL_UNAVAILABLE)

            if 'h' in datum:
                shelfmark = datum['h'][0]
                if 't' in datum:
                    shelfmark = "%s (copy %s)" % (shelfmark, datum['t'][0])
            elif 't' in datum:
                shelfmark = "Copy %s" % datum['t'][0]
            else:
                shelfmark = None

            materials_specified = datum['3'][0] if '3' in datum else None

            if not library in self.libraries:
                self.libraries[library] = []
            self.libraries[library].append( {
                'due': due_date,
                'availability': availability,
                'availability_display': datum['y'][0] if 'y' in datum else None,
                'shelfmark': shelfmark,
                'materials_specified': materials_specified,
            } )

        for library in self.libraries:
            library.availability = max(l['availability'] for l in self.libraries[library])

    def simplify_for_render(self, simplify_value, simplify_model):
        return {
            '_type': 'z3950.Item',
            '_pk': self.control_number,
            'title': self.title,
            'publisher': self.publisher,
            'author': self.author,
            'description': self.description,
            'edition': self.edition,
            'copies': self.copies,
            'holding_libraries': self.holding_libraries,
            'isbns': simplify_value(self.isbns()),
            'issns': simplify_value(self.issns()),
            'holdings': simplify_value(self.libraries),
        }

    def _metadata_property(heading, sep=' '):
        def f(self):
            if not heading in self.metadata:
                    return None
            field = self.metadata[heading][0]
            return sep.join(' '.join(field[k]) for k in sorted(field))
        return property(f)

    title = _metadata_property(USM_TITLE_STATEMENT)
    publisher = _metadata_property(USM_PUBLICATION)
    author = _metadata_property(USM_AUTHOR)
    description = _metadata_property(USM_PHYSICAL_DESCRIPTION)
    edition = _metadata_property(USM_EDITION)
    copies = property(lambda self: len(self.metadata[OLISResult.USM_LOCATION]))
    holding_libraries = property(lambda self: len(self.libraries))

    def isbns(self):
        if OLISResult.USM_ISBN in self.metadata:
            return [a.get('a', ["%s (invalid)" % a.get('z', ['Unknown'])[0]])[0] for a in self.metadata[OLISResult.USM_ISBN]]
        else:
            return []

    def issns(self):
        if OLISResult.USM_ISSN in self.metadata:
            return [a['a'][0] for a in self.metadata[OLISResult.USM_ISSN]]
        else:
            return []

    def __unicode__(self):
        return self.title

def marc_to_unicode(x):
    translator = MARC8_to_Unicode()
    def f(y):
        if isinstance(y, dict):
            return dict((k,f(y[k])) for k in y)
        elif isinstance(y, tuple):
            return tuple(f(e) for e in y)
        elif isinstance(y, list):
            return [f(e) for e in y]
        elif isinstance(y, str):
            if any((ord(c) > 127) for c in y):
                # "The ESC character 0x1B is mapped to the no-break space
                #  character, unless it is part of a valid ESC sequence"
                #      -- http://unicode.org/Public/MAPPINGS/ETSI/GSM0338.TXT
                return translator.translate(y).replace(u'\x1b', u'\xa0')
            else:
                return y.decode('ascii').replace(u'\x1b', u'\xa0')
    return f(x)

class ISBNOrISSNSearch(OLISSearch):
    def __init__(self, number, conf, number_type=None):
        if not number_type:
            number, number_type = validate_isxn(number)
        if number_type == 'issn':
            # It's actually an ISSN
            query = '(1,8)=%s' % number
        else:
            query = 'isbn=%s' % number
        super(ISBNOrISSNSearch, self).__init__(query, conf)

class ControlNumberSearch(OLISSearch):
    def __init__(self, control_number, conf):
        query = '(1,1032)="%s"' % control_number
        super(ControlNumberSearch, self).__init__(query, conf)

def isxn_checksum(s, initial=None):
    if not initial:
        initial = len(s)
    cs = 0
    for d in s:
        cs, initial = (cs + (d*initial)) % 11, initial - 1
    return cs

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
class SiteSearch(object):
    def __new__(cls, query, only_app, request):
        number, number_type = validate_isxn(query)
        if not number_type:
            return [], False, None

        results, items = [], ISBNOrISSNSearch(number, number_type)
        for item in items:
            results.append({
                'title': item.title,
                'redirect_if_sole_result': True,
                'application': 'z3950',
                'excerpt': '',
                'additional': '<strong>Library item</strong>, Publisher: %s' % item.publisher,
                'url': reverse('z3950_item_detail', args=[item.control_number]),
            })

        return results, False, None
