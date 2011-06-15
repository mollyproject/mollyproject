"""
TODO:

* finish merging from archives app
* Add documentation
* change to support pagination how the library app expects it (lazily evaluated object)
* change library search to use custom forms (from archives app)
"""

import httplib
import logging
import socket
import time
import urllib
import urllib2
from lxml import etree, objectify

from django.utils.translation import ugettext_lazy

from molly.apps.library.models import LibrarySearchResult, Library
from molly.apps.library.providers import BaseLibrarySearchProvider

NSMAP = {'sru': "http://www.loc.gov/zing/srw/",
         'srw_dc': "info:srw/schema/1/dc-v1.1",
         'dc': "http://purl.org/dc/elements/1.0",
         'diag': "http://www.loc.gov/zing/srw/diagnostic/"
         }

class SRUSearchResult(LibrarySearchResult):

    def __init__(self, sruRecord):
        self.sruRecord = sruRecord
        print self
    
    def __repr__(self):
        return self.sruRecord.recordData.toxml()

    def _sru_getattr(self, name):
        NSMAP.update({'rec': "http://www.cheshire3.org/srw/extension/2/record-1.1"})
        if name == 'id':
            xpath = './/dc:identifier'
        elif name == 'title':
            xpath = './/dc:title'
        elif name == 'collectionId':
            xpath = '..//rec:collectionIdentifier'
        elif name == 'author':
            xpath = '..//dc:creator'
        elif name == 'date':
            xpath = './/dc:date'
        elif name == 'description':
            xpath = './/dc:description'
        else:
            raise AttributeError(name)
        els = self.sruRecord.recordData.xpath(xpath, namespaces=NSMAP)
        return ' '.join([etree.tostring(el, method='text') for el in els])
    
    @property
    def id(self):
        return self._sru_getattr('id')
    
    @property
    def control_number(self):
        return self.sruRecord.recordData.xpath('.')[0].attrib['id']
    
    @property
    def title(self):
        return self._sru_getattr('title')
    
    publisher = None
    
    @property
    def author(self):
        return self._sru_getattr('author')
    
    @property
    def description(self):
        return self._sru_getattr('description')
    
    @property
    def edition(self):
        return self._sru_getattr('date')
    
    edition = None
    copies = 1
    holding_libraries = 1
    isbns = []
    issns = []
    
    @property
    def holdings(self):
        return {
            Library((self._sru_getattr('collectionId'),)): {
                'due': None,
                'availability': LibrarySearchResult.AVAIL_UNKNOWN,
                'availability_display': ugettext_lazy('Unknown'),
                'shelfmark': None,
                'materials_specified': self._sru_getattr('date'),
            }
        }

class SRU(BaseLibrarySearchProvider):
    
    class Results:
        """
        A thing that pretends to be a list for lazy parsing of search results
        """
        
        def __init__(self, results, wrapper):
            self.results = results
            self._wrapper = wrapper
        
        def __iter__(self):
            for result in self.results:
                yield self._wrapper(result)
        
        def __len__(self):
            return len(self.results)
        
        def __getitem__(self, key):
            if isinstance(key, slice):
                if key.step:
                    raise NotImplementedError("Stepping not supported")
                return map(self._wrapper,
                           self.results.__getslice__(key.start, key.stop))
            else:
                return self._wrapper(self.results[key])
    
    def __init__(self, host, port, database, version=1.2):
        """
        @param host: The hostname of the SRU to connect to
        @type host: str
        @param port: The server port
        @type port: int
        @param database: The database name
        @type database: str
        @param version: The version to request an answer for
        @type version: float
        """
        self.target = "http://{0}:{1}/{2}".format(host, port, database)
        self.params = {'version': version}
    
    def library_search(self, query):
        """
        @param query: The query to be performed
        @type query: molly.apps.library.models.LibrarySearchQuery
        @return: A list of results
        @rtype: [LibrarySearchResult]
        """
        
        query = '{0} {1} "{2}"'.format('cql.anywhere', 'all/rel.algorithm=okapi', query.title)
        
        params = self.params
        # searchRetrieve defaults
        params.update({'operation': 'searchRetrieve',
                       'maximumRecords': 10,
                       'startRecord': 1, # SRU starts at record 1 not 0z
                       'recordSchema': 'dc'
                       })
        # add query
        params['query'] = query.encode('utf-8')
        url = "{0}?{1}".format(self.target, urllib.urlencode(params))
        resp = get_searchRetrieveResponse(url)
        if resp is None:
            raise Exception("Could not carry out search from SRU target {0}".format(self.target))
        rsis = []
        if resp is None:
            raise ValueError('Did not get response from server.')
        for res in resp.records:
            rsis.append(SRUSearchResult(res))
        return rsis
    
    def control_number_search(self, control_number):
        """
        @param control_number: The unique ID of the item to be looked up
        @type control_number: str
        @return: The item with this control ID, or None if none can be found
        @rtype: LibrarySearchResult
        """
        
        raise NotImplementedError()


class SruObject:
    """ Abstract class for objectifying SRU XML
    ZSI attrs: name, typecode
    """
    
    tree = None
    
    def __dir__(self):
        attrlist = dir(self) 
        attrlist.extend(['name', 'typecode'])
        attrlist.sort()
        return  attrlist
    
    def __init__(self, node):
        self.tree = node
    
    def __getattr__(self, name):
        # avoid command line repr wierdness
        if name == '__repr__':
            raise AttributeError
        elif name == 'attrib':
            return self.tree.attrib
        elif name == 'name':
            return self.tag[self.tag.find('}')+1:]
        elif name =='typecode':
            return

        return getattr(self.tree, name)    

    def __str__(self):
#        return objectify.dump(self.tree)
        return etree.tostring(self.tree)


class SruRecord(SruObject):
    """ Thin wrapper for records returned in SRU responses. 
    Note: Not the same as a Cheshire3 Record - although the recordData could be used to construct one...
    ZSI attrs (additional): inline, recordData, recordPacking, recordPosition, recordSchema
    """
    
    def __dir__(self):
        attrlist = SruObject.__dir__(self) 
        attrlist.extend(['inline', 'recordData', 'recordPacking', 'recordPosition', 'recordSchema'])
        attrlist.sort()
        return  attrlist
    
    def __getattr__(self, name):
        if name == 'recordData':
            if self.recordPacking == 'string':
                return SruRecordData(objectify.fromstring(str(self.tree.recordData)))
            else:
                # default: recordPacking == 'xml'
                return SruRecordData(self.tree.recordData.getchildren()[0])

        return SruObject.__getattr__(self, name)


class SruRecordData(SruObject):
    
    def __dir__(self):
        attrlist = SruObject.__dir__(self) 
        attrlist.extend(['toxml'])
        attrlist.sort()
        return  attrlist
    
    def __getattr__(self, name):
        if name == 'id':
            try:
                return self.tree.attrib['id']
            except KeyError:
                pass
        else:
            return SruObject.__getattr__(self, name)
    
    def toxml(self):
        return etree.tostring(self.tree)
    

class SruResponse(SruObject):
    """ Abstract class for SRU responses
    ZSI attrs (additional): diagnostics, extraResponseData, version
    """
    
    def __dir__(self):
        attrlist = SruObject.__dir__(self) 
        attrlist.extend(['diagnostics', 'extraResponseData', 'version'])
        attrlist.sort()
        return  attrlist
    
    def __getattr__(self, name):
        if name == 'diagnostics':
            try:
                diags = SruObject.__getattr__(self, name) 
                return [ el for el in diags.iterchildren(tag='{http://www.loc.gov/zing/srw/diagnostic/}diagnostic') ]
            except AttributeError:
                return []

        return SruObject.__getattr__(self, name)

    
class ExplainResponse(SruResponse):
    """ Thin wrapper for SRU Explain Response
    ZSI attrs (additional): echoedExplainRequest, record
    """ 
    
    def __dir__(self):
        attrlist = SruResponse.__dir__(self) 
        attrlist.extend(['echoedExplainRequest', 'record'])
        attrlist.sort()
        return  attrlist
    
    def __getattr__(self, name):
        if name == 'record':
            return SruRecord(self.tree.record)
        
        return SruResponse.__getattr__(self, name)
            
    def __str__(self):
        return objectify.dump(self.tree)
        #return "%s:\n    Version: %s\n    Record (presence of): %i\n    Diagnostics: %s\n    ExtraResponseData: %s" % (self.__class__.__name__, self.version, self.record <> None, repr(self.diagnostics), repr(self.extraResponseData))
        

class SearchRetrieveResponse(SruResponse):
    """ Thin wrapper for SRU SearchRetrieve Response
    ZSI attrs (additional): echoedSearchRetrieveRequest, numberOfRecords, records, nextRecordPosition, resultSetId, resultSetIdleTime
    """
    
    def __dir__(self):
        attrlist = SruResponse.__dir__(self) 
        attrlist.extend(['echoedSearchRetrieveRequest', 'nextRecordPosition', 'numberOfRecords', 'records', 'resultSetId', 'resultSetIdleTime'])
        attrlist.sort()
        return attrlist
           
    def __getattr__(self, name):
        if name == 'records':
            try:
                return [SruRecord(el) for el in self.tree.records.record]
            except AttributeError:
                return []
    
        return SruResponse.__getattr__(self, name)
        
    
class ScanResponse(SruResponse):
    """ Thin wrapper for SRU Scan Response
    ZSI attrs (additional): echoedScanRequest, terms
    """
    def __dir__(self):
        attrlist = SruResponse.__dir__(self) 
        attrlist.extend(['echoedscanRequest', 'terms'])
        attrlist.sort()
        return  attrlist
    
    def __getattr__(self, name):
        if name == 'terms':
            try:
                return [el for el in self.tree.terms.term]
            except AttributeError:
                return []

        return SruResponse.__getattr__(self, name)
    

def fetch_data(myUrl, tries=1, timeout=20):
    oldtimeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(timeout)
    req = urllib2.Request(url=myUrl)
    data = None
    for x in range(tries):
        try:
            f = urllib2.urlopen(req)
        except (urllib2.URLError):
            # problem accessing remote service
            continue
        except httplib.BadStatusLine:
            # response broken
            time.sleep(0.5)
            continue
        except socket.timeout:
            time.sleep(0.5)
            continue
        else:
            data = f.read()
            f.close()
            break

    socket.setdefaulttimeout(oldtimeout)
    return data


objectifier = objectify.makeparser(remove_blank_text=False)


# functions to fetch and return a parsed response object when given a URL
def get_explainResponse(url, tries=1, timeout=20):
    """Fetch, objectify and return an SRU explain request."""
    data = fetch_data(url, tries=tries, timeout=timeout)
    if data is not None:
        tree = objectify.fromstring(data, objectifier)
        return ExplainResponse(tree)
        

def get_searchRetrieveResponse(url, tries=1, timeout=20):
    """Fetch, objectify and return an SRU searchRetrieve request."""
    data = fetch_data(url, tries=tries, timeout=timeout)
    if data is not None:
        tree = objectify.fromstring(data, objectifier)
        return SearchRetrieveResponse(tree)

    
def get_scanResponse(url, tries=1, timeout=20):
    """Fetch, objectify and return an SRU scan request."""
    data = fetch_data(url, tries=tries, timeout=timeout)
    if data is not None:
        tree = objectify.fromstring(data, objectifier)
        return ScanResponse(tree)