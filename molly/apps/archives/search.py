"""Search the Archives Hub."""

import sys

from lxml import etree, objectify


from molly.apps.archives.providers.sru import NSMAP

sys.path.insert(1, '/home/johnph/mollyproject')

class ArchivesSearchResult(object):
    provider = None
    numberOfResults = 0
    resultSetItems = []
    
    def __init__(self, req, query, conf, **kwargs):
        pass





class ArchivesSearchResultSetItem(SruSearchResultSetItem):
    
    def __getattr__(self, name):
        if name == 'id':
            finder = objectify.ObjectPath('/ead/archdesc/did/unitid'.format(**NSMAP))
        elif name == 'title':
            finder = objectify.ObjectPath('/ead/archdesc/did/unittitle'.format(**NSMAP))
        elif name == 'creator':
            finder = objectify.ObjectPath('/ead/archdesc/did/origination'.format(**NSMAP))
        elif name == 'date':
            finder = objectify.ObjectPath('/ead/archdesc/did/unitdate'.format(**NSMAP))
        elif name == 'description':
            finder = objectify.ObjectPath('/ead/archdesc/scopecontent'.format(**NSMAP))
        try:
            return finder.find(self.data)
        except (ValueError, NameError):
            return getattr(super(SruSearchResultSetItem), name)
