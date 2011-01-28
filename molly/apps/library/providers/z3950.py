from datetime import datetime

from PyZ3950 import zoom
from PyZ3950.zmarc import MARC, MARC8_to_Unicode

from molly.apps.library.models import LibrarySearchResult, Library
from molly.apps.library.providers import BaseLibrarySearchProvider

class Z3950(BaseLibrarySearchProvider):
    
    class SearchResult(LibrarySearchResult):
        USM_CONTROL_NUMBER = 1
        USM_ISBN = 20
        USM_ISSN = 22
        USM_AUTHOR = 100
        USM_TITLE_STATEMENT = 245
        USM_EDITION = 250
        USM_PUBLICATION = 260
        USM_PHYSICAL_DESCRIPTION = 300
        USM_LOCATION = 852
        
        AVAILABILITIES = {
            'Available': LibrarySearchResult.AVAIL_AVAILABLE,
            'Reference': LibrarySearchResult.AVAIL_REFERENCE,
            'Confined': LibrarySearchResult.AVAIL_REFERENCE,
            'Check shelf': LibrarySearchResult.AVAIL_UNKNOWN,
            'Please check shelf': LibrarySearchResult.AVAIL_UNKNOWN,
            'In place': LibrarySearchResult.AVAIL_STACK,
            'Missing': LibrarySearchResult.AVAIL_UNAVAILABLE,
            'Temporarily missing': LibrarySearchResult.AVAIL_UNAVAILABLE,
            'Reported Missing': LibrarySearchResult.AVAIL_UNAVAILABLE,
            'Withdrawn': LibrarySearchResult.AVAIL_UNAVAILABLE,
            '': LibrarySearchResult.AVAIL_UNKNOWN,
        }
    
        def __init__(self, result):
            self.str = str(result)
            self.metadata = {self.USM_LOCATION: []}
    
            items = self.str.split('\n')[1:]
            for item in items:
                heading, data = item.split(' ', 1)
                heading = int(heading)
                if heading == self.USM_CONTROL_NUMBER:
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
    
            for datum in self.metadata[self.USM_LOCATION]:
                library = Library(datum['b'])
                if not 'p' in datum:
                    availability = LibrarySearchResult.AVAIL_UNKNOWN
                    datum['y'] = ['Check web OPAC']
                    due_date = None
                elif not 'y' in datum:
                    due_date = None
                    availability = LibrarySearchResult.AVAIL_UNKNOWN
                elif datum['y'][0].startswith('DUE BACK: '):
                    due_date = datetime.strptime(datum['y'][0][10:], '%d/%m/%y')
                    availability = LibrarySearchResult.AVAIL_UNAVAILABLE
                else:
                    due_date = None
                    availability = self.AVAILABILITIES.get(datum['y'][0],
                                        LibrarySearchResult.AVAIL_UNAVAILABLE)
    
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
        copies = property(lambda self: len(self.metadata[self.USM_LOCATION]))
        holding_libraries = property(lambda self: len(self.libraries))
    
        def isbns(self):
            if self.USM_ISBN in self.metadata:
                return [a.get('a', ["%s (invalid)" % a.get('z', ['Unknown'])[0]])[0] for a in self.metadata[self.USM_ISBN]]
            else:
                return []
    
        def issns(self):
            if self.USM_ISSN in self.metadata:
                return [a['a'][0] for a in self.metadata[self.USM_ISSN]]
            else:
                return []
    
    class Results:
        """
        A thing that pretends to be a list for lazy parsing of search results
        """
        
        def __init__(self, results):
            self.results = results
        
        def __iter__(self):
            for result in self.results:
                yield Z3950.SearchResult(result)
        
        def __len__(self):
            return len(self.results)
        
        def __getitem__(self, key):
            if isinstance(key, slice):
                if key.step:
                    raise NotImplementedError("Stepping not supported")
                return map(Z3950.SearchResult,
                           self.results.__getslice__(key.start, key.stop))
            else:
                return Z3950.SearchResult(self.results[key])
    
    def __init__(self, host, database, port=210, syntax='USMARC', charset='UTF-8'):
        """
        @param host: The hostname of the Z39.50 instance to connect to
        @type host: str
        @param database: The database name
        @type database: str
        @param port: An optional port for the Z39.50 database
        @type port: int
        @param syntax: The Z39.50 syntax to use
        @type syntax: str
        @param charset: The charset to make the connection in
        @type charset: str
        """
        
        # Could create a persistent connection here
        self._host = host
        self._database = database
        self._port = port
        self._syntax = syntax
        self._charset = charset
    
    def _make_connection(self):
        """
        Returns a connection to the Z39.50 server
        """
        # Create connection to database
        connection = zoom.Connection(
            self._host,
            self._port,
            charset = self._charset,
        )
        connection.databaseName = self._database
        connection.preferredRecordSyntax = self._syntax
        
        return connection
    
    def library_search(self, query):
        """
        @param query: The query to be performed
        @type query: molly.apps.library.models.LibrarySearchQuery
        @return: A list of results
        @rtype: [LibrarySearchResult]
        """
        
        connection = self._make_connection()
        
        # Convert Query object into a Z39.50 query - we escape for the query by
        # removing quotation marks
        z3950_query = []
        if query.author != None:
            z3950_query.append('(au="%s")' % query.author.replace('"', ''))
        if query.title != None:
            z3950_query.append('(ti="%s")' % query.title.replace('"', ''))
        if query.isbn != None:
            z3950_query.append('(isbn="%s")' % query.isbn.replace('"', ''))
        
        z3950_query = zoom.Query('CCL', 'and'.join(z3950_query))
        
        results = self.Results(connection.search(z3950_query))
        return results
    
    def control_number_search(self, control_number):
        """
        @param control_number: The unique ID of the item to be looked up
        @type control_number: str
        @return: The item with this control ID, or None if none can be found
        @rtype: LibrarySearchResult
        """
        
        # Escape input
        control_number = control_number.replace('"', '')
        
        z3950_query = zoom.Query('CCL', '(1,1032)="%s"' % control_number)
        connection = self._make_connection()
        results = self.Results(connection.search(z3950_query))
        if len(results) > 0:
            return results[0]
        else:
            return None

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