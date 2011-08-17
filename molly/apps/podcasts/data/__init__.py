import rdflib
import os.path

__all__ = ['licenses']

FOAF = rdflib.Namespace('http://xmlns.com/foaf/0.1/')
DCTERMS = rdflib.Namespace('http://purl.org/dc/terms/')
DCTYPE = rdflib.Namespace('http://purl.org/dc/dcmitype/')
RDF = rdflib.Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')

class _License(object):
    def __init__(self, graph, uri):
        self._graph, self._uri = graph, uri
    
    def get(self, p):
        for o in self._graph.objects(self._uri, p):
            return unicode(o)
        return None
    
    def __unicode__(self):
        return self.get(DCTERMS['title'])

    @property
    def logo(self):
        return self.get(FOAF['logo'])
    
    def simplify_for_render(self, simplify_value, simplify_model):
        simplified = {}
        for predicate, object in self._graph.predicate_objects(self._uri):
            # Disregard type
            if predicate == RDF['type']:
                continue
            
            # Convert predicate URIs into something a bit friendlier
            predicate = {
                DCTERMS['title']: 'title',
                FOAF['logo']: 'logo',
                DCTERMS['description']: 'description',
            }.get(predicate, predicate)
            simplified[predicate] = simplify_value(object)
        return simplified

class _Licenses(object):
    def __init__(self, filename):
        self._data = rdflib.ConjunctiveGraph()
        self._data.parse(open(filename, 'r'), format='n3')
    
    def get(self, uri):
        uri = rdflib.URIRef(uri)
        if (uri, RDF['type'], DCTYPE['LicenseDocument']) in self._data:
            return _License(self._data, uri)
        else:
            return None

licenses = _Licenses(os.path.join(os.path.dirname(__file__), 'source', 'licenses.n3'))
