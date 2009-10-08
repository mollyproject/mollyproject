import re, urllib, simplejson
from datetime import datetime
from PyZ3950 import zoom

from django.conf import settings

from mobile_portal.oxpoints.models import Entity

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
    'Withdrawn': AVAIL_UNAVAILABLE,
    '': AVAIL_UNKNOWN,
}
def require_json(f):
    def g(self, *args, **kwargs):
        try:
            if not hasattr(self, '_json'):
                self._json = simplejson.load(urllib.urlopen(
                    Library.LIBRARY_URL % self.location[-1].replace(' ', '+')
                ))[0]
        except:
            self._json = None
        return f(self, *args, **kwargs)
    return g
 
class Library(object):
    LIBRARY_URL = "http://m.ox.ac.uk/oxpoints/hasOLISCode/%s.json"
    def __init__(self, location):
        self.location = tuple(location)
       
    @property
    def oxpoints_id(self):
        def f(self):
            return int(self._json['uri'][-8:])

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
            self._oxpoints_entity = Entity.objects.get(oxpoints_id=self.oxpoints_id)
            return self._oxpoints_entity
            
    @property
    @require_json
    def oxpoints_location(self):
        return self.oxpoints_entity.location
    
    @require_json
    def __unicode__(self):
        if self.oxpoints_id:
            return "%s (%d)" % (self.oxpoints_entity.title, self.oxpoints_id)
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
        self.result = result
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
                m[subfield_id].append(content.decode('iso-8859-1'))
            self.metadata[heading].append(m)

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
            return [a['a'][0] for a in self.metadata[OLISResult.USM_ISBN]]
        else:
            return []
    
    def issns(self):
        if OLISResult.USM_ISSN in self.metadata:
            return [a['a'][0] for a in self.metadata[OLISResult.USM_ISSN]]
        else:
            return []
    
    def __unicode__(self):
        return self.title

class OLISSearch(object):
    def __init__(self, query):
        self.connection = zoom.Connection(
            getattr(settings, 'Z3950_HOST'),
            getattr(settings, 'Z3950_PORT', 210),
        )
        self.connection.databaseName = getattr(settings, 'Z3950_DATABASE')
        self.connection.preferredRecordSyntax = getattr(settings, 'Z3950_SYNTAX', 'USMARC')
        
        self.query = zoom.Query('CCL', query)
        
        self.results = self.connection.search(self.query)
        
    def __iter__(self):
        for r in self.results:
            yield OLISResult(r)
        
    def __len__(self):
        return len(self.results)        

    def __getitem__(self, key):
        if isinstance(key, slice):
            if key.step:
                raise NotImplementedError("Stepping not supported")
            return map(OLISResult, self.results.__getslice__(key.start, key.stop))
        return OLISResult(self.results[key])        
        
class ISBNSearch(OLISSearch):
    def __init__(self, isbn):
        query = 'isbn=%s' % isbn
        super(ISBNSearch, self).__init__(query)

class ControlNumberSearch(OLISSearch):
    def __init__(self, control_number):
        query = '(1,1032)="%s"' % control_number
        super(ControlNumberSearch, self).__init__(query)
