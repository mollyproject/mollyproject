import logging

import suds, suds.sudsobject

logger = logging.getLogger('molly.providers.apps.places.ldb')

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
        
        try:
            ldb = suds.client.Client(self._WSDL_URL)
        except Exception, e:
            logger.warning("Could not instantiate suds client for live departure board.", exc_info=True, extra={'wsdl_url': self._WSDL_URL})
            self._add_error(station_entities)
            return
        
        for entity in station_entities:
            try:
                db = ldb.service.GetDepartureBoard(self._max_services, entity.identifiers['crs'])
            except Exception, e:
                logger.warning("Could not retrieve departure board for station: %r", entity.identifiers.get('crs'), crs_code=entity.identifiers.get('crs'))
                self._add_error(station_entities)
                return
            
            entity.metadata['ldb'] = self.transform_suds(db)
            
    def transform_suds(self, o):
        if isinstance(o, suds.sudsobject.Object):
            return dict((k, self.transform_suds(v)) for k,v in o)
        elif isinstance(o, list):
            return map(self.transform_suds, o)
        else:
            return o

    def _add_error(self, entities):
        for entity in entities:
            entity.metadata['ldb'] = {'error': True}