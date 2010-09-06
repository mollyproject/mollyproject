import suds, suds.sudsobject

from molly.apps.places.providers import BaseMapsProvider

class LiveDepartureBoardPlacesProvider(BaseMapsProvider):
    _WSDL_URL = "http://realtime.nationalrail.co.uk/ldbws/wsdl.aspx"
    
    def __init__(self, max_services=10, max_results=1):
        self._max_services = max_services
        self._max_results = max_results

    def augment_metadata(self, entities):
        station_entities = []
        for entity in entities:
            if not entity.identifiers.get('crs'):
                continue
            station_entities.append(entity)

        station_entities = station_entities[:self._max_results]
        if not station_entities:
            return
        
        ldb = suds.client.Client(self._WSDL_URL)
        
        for entity in station_entities:
            db = ldb.service.GetDepartureBoard(self._max_services, entity.identifiers['crs'])
            
            entity.metadata['ldb'] = self.transform_suds(db)
            
    def transform_suds(self, o):
        if isinstance(o, suds.sudsobject.Object):
            return dict((k, self.transform_suds(v)) for k,v in o)
        elif isinstance(o, list):
            return map(self.transform_suds, o)
        else:
            return o
