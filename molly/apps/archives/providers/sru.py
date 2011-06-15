"""SRU Provider and utils for Molly.

Author:    John Harrison <john.harrison@liverpool.ac.uk>
Date:      17th February 2011
Copyright: University of Liverpool, 2011
Description:
    SRU Provider for Molly and associated helper functions and utils.

Some examples:

Constructor
>>> sruProvider = SruProvider('archiveshub.ac.uk', 80, 'api/sru/hub')
>>> sruProvider.target
'http://archiveshub.ac.uk:80/api/sru/hub'

Explain request:

>>> resp = sruProvider.perform_explain(None)
>>> isinstance(resp, ExplainResponse)
True

Scan request:

>>> maxTerms = 10
>>> resp = sruProvider.perform_scan(None, 'dc.title = "a"', application=None, maximumTerms=maxTerms)
>>> isinstance(resp, ScanResponse)
True
>>> len(resp.terms) <= maxTerms
True

Search request:

>>> maxRecs = 10
>>> resp = sruProvider.perform_search(None, 'dc.description all "liverpool university papers"', application=None, maximumRecords=maxRecs)
>>> isinstance(resp, SearchRetrieveResponse)
True
>>> len(resp.records) <= maxRecs
True
"""

import httplib
import logging
import socket
import time
import urllib
import urllib2

from lxml import etree, objectify

from molly.apps.search.providers import BaseSearchProvider

logger = logging.getLogger('molly.providers.apps.search.sru')

NSMAP = {'sru': "http://www.loc.gov/zing/srw/",
         'srw_dc': "info:srw/schema/1/dc-v1.1",
         'dc': "http://purl.org/dc/elements/1.0",
         'diag': "http://www.loc.gov/zing/srw/diagnostic/"
         }
    

class SruProvider(BaseSearchProvider):
    """SRU Provider for use with molly."""
    
    def __init__(self, host, port, database, version=1.2):
        self.target = "http://{0}:{1}/{2}".format(host, port, database)
        self.params = {'version': version}
        
    def perform_explain(self, application=None, **kwargs):
        """Do an explain request, return a response object.
        
        >>> sruProvider = SruProvider('archiveshub.ac.uk', 80, 'api/sru/hub')
        >>> resp = sruProvider.perform_explain(None)
        >>> isinstance(resp, ExplainResponse)
        True
        """
        params = self.params
        # scan defaults
        params.update({'operation': 'explain'})
        # over-ride defaults with kwargs
        params.update(kwargs)
        url = "{0}?{1}".format(self.target, urllib.urlencode(params))
        logger.debug(url)
        resp = get_explainResponse(url)
        if resp is None:
            logger.exception("Could not fetch explain response from SRU target {0}".format(self.target))
        # TODO: check for fault diagnostics
        return resp
        
    def perform_scan(self, scanClause, application=None, **kwargs):
        """Do a scan request, return a response request.
        
        >>> sruProvider = SruProvider('archiveshub.ac.uk', 80, 'api/sru/hub')
        >>> maxTerms = 10
        >>> resp = sruProvider.perform_scan(None, 'dc.title = "a"', application=None, maximumTerms=maxTerms)
        >>> isinstance(resp, ScanResponse)
        True
        >>> len(resp.terms) <= maxTerms
        True
        """
        params = self.params
        # scan defaults
        params.update({'operation': 'scan',
                       'maximumTerms': 20,
                       'responsePosition': 10
                       })
        # over-ride defaults with kwargs
        params.update(kwargs)
        # add query
        params['scanClause'] = scanClause.encode('utf-8')
        url = "{0}?{1}".format(self.target, urllib.urlencode(params))
        logger.debug(url)
        resp = get_scanResponse(url)
        if resp is None:
            logger.exception("Could not carry out scan from SRU target {0}".format(self.target))
        # TODO: check for fault diagnostics
        return resp
        
    def perform_search(self, query, application=None, **kwargs):
        """Do a search request, return a response object.
        
        >>> sruProvider = SruProvider('archiveshub.ac.uk', 80, 'api/sru/hub')
        >>> maxRecs = 10
        >>> resp = sruProvider.perform_search(None, 'dc.description all "liverpool university papers"', application=None, maximumRecords=maxRecs)
        >>> isinstance(resp, SearchRetrieveResponse)
        True
        >>> len(resp.records) <= maxRecs
        True
        """
        params = self.params
        # searchRetrieve defaults
        params.update({'operation': 'searchRetrieve',
                       'maximumRecords': 10,
                       'startRecord': 1, # SRU starts at record 1 not 0
                       'recordSchema': 'dc'
                       })
        # over-ride defaults with kwargs
        params.update(kwargs)
        # add query
        params['query'] = query.encode('utf-8')
        url = "{0}?{1}".format(self.target, urllib.urlencode(params))
        logger.debug(url)
        resp = get_searchRetrieveResponse(url)
        if resp is None:
            logger.exception("Could not carry out search from SRU target {0}".format(self.target))
        # TODO: check for fault diagnostics
        rsis = []
        if resp is None:
            raise ValueError('Did not get response from server.')
        for res in resp.records:
            rsis.append(SruSearchResultSetItem(res))
        return rsis


class SruSearchResultSetItem(object):
    
    def __init__(self, sruRecord):
        self.sruRecord = sruRecord
    
    def __repr__(self):
        return self.sruRecord.recordData.toxml()
        
    def __getattr__(self, name):
        NSMAP.update({'rec': "http://www.cheshire3.org/srw/extension/2/record-1.1"})
        if name == 'id':
            xpath = './/dc:identifier'
        elif name == 'title':
            xpath = './/dc:title'
        elif name == 'collectionId':
            xpath = '..//rec:collectionIdentifier'
        elif name == 'creator':
            xpath = '..//dc:creator'
        elif name == 'date':
            xpath = './/dc:date'
        elif name == 'description':
            xpath = './/dc:description'
        else:
            raise AttributeError(name)
        els = self.sruRecord.recordData.xpath(xpath, namespaces=NSMAP)
        return ' '.join([etree.tostring(el, method='text') for el in els])
    
    
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


if __name__ == "__main__":
    import doctest
    doctest.testmod()
