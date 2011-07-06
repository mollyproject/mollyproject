import logging
import suds, suds.sudsobject
from suds.sax.element import Element

from django.utils.translation import ugettext_lazy

from molly.apps.places.models import Entity
from molly.apps.places.providers import BaseMapsProvider

logger = logging.getLogger(__name__)

class LiveDepartureBoardPlacesProvider(BaseMapsProvider):
    _WSDL_URL = "http://realtime.nationalrail.co.uk/ldbws/wsdl.aspx"
    
    def __init__(self, token, max_services=15, max_results=1):
        self._max_services = max_services
        self._max_results = max_results
        self._token = token

    def augment_metadata(self, entities, board='departures', **kwargs):
        station_entities = []
        for entity in entities:
            if not entity.identifiers.get('crs'):
                continue
            station_entities.append(entity)

        station_entities = station_entities[:self._max_results]
        if not station_entities:
            return
        
        try:
            ldb = suds.client.Client(self._WSDL_URL, soapheaders=Element('AccessToken').insert(Element('TokenValue').setText(self._token)))
        except Exception, e:
            logger.warning("Could not instantiate suds client for live departure board.", exc_info=True, extra={'wsdl_url': self._WSDL_URL})
            self._add_error(station_entities)
            return
        
        for entity in station_entities:
            try:
                if board == 'arrivals':
                    db = ldb.service.GetArrivalBoard(self._max_services, entity.identifiers['crs'])
                else:
                    db = ldb.service.GetDepartureBoard(self._max_services, entity.identifiers['crs'])
                db = self.transform_suds(db)
                entity.metadata['ldb'] = db
                entity.metadata['service_details'] = lambda s: LiveDepartureBoardPlacesProvider.service_details(s, entity)
                entity.metadata['ldb_service'] = lambda s: self.transform_suds(ldb.service.GetServiceDetails(s))
                entity.metadata['service_type'] = 'ldb'
                
                # Show bus services too
                if board == 'arrivals':
                    db = self.transform_suds(
                        ldb.service.GetDepartureBoard(self._max_services,
                                                     entity.identifiers['crs']))
                
                if 'busServices' in db:
                    for service in db['busServices']['service']:
                        entity.metadata['real_time_information'] = {
                            'services':
                                [{
                                    'service': 'BUS',
                                    'destination': service['destination']['location'][0]['locationName'],
                                    'next': service['std'],
                                    'following': [],
                                }]
                        }
                
            except Exception, e:
                logger.warning("Could not retrieve departure board for station: %r", entity.identifiers.get('crs'))
                self._add_error((entity,))
            entity.metadata['meta_refresh'] = 60
    
    @staticmethod
    def service_details(service, entity):
        try:
            service = entity.metadata['ldb_service'](service)
        except suds.WebFault as f:
            if f.fault['faultstring'] == 'Unexpected server error: Invalid length for a Base-64 char array.':
                raise Http404
            else:
                return({'error': f.fault['faultstring']})
        if service is None:
            return None
        
        # Trains can split and join, which makes figuring out the list of
        # calling points a bit difficult. The LiveDepartureBoards documentation
        # details how these should be handled. First, we build a list of all
        # the calling points on the "through" train.
        calling_points = service['previousCallingPoints']['callingPointList'][0]['callingPoint'] if len(service['previousCallingPoints']) else []

        # Then attach joining services to our thorough route in the correct
        # point, but only if there is a list of previous calling points
        if len(service['previousCallingPoints']):
            for i, points in enumerate(service['previousCallingPoints']['callingPointList'][1:]):
                # If the other half of the split ends up here, it's not a split, but
                # a change between rail replacement bus of train
                for j, point in enumerate(calling_points):
                    if points['callingPoint'][-1]['crs'] == point['crs']:
                        if j > 0:
                            point['joining'] = points['callingPoint']
                        else:
                            point['service_change'] = service['previousCallingPoints']['callingPointList'][i]['_serviceType']
                            calling_points = points['callingPoint'] + calling_points
                            break
        
        # Add our current station
        calling_points += [{
            'locationName': service['locationName'],
            'crs': service['crs'],
            'st': service['std'] if 'std' in service else service['sta'],
            'et': service['etd'] if 'etd' in service else service['eta'] if 'eta' in service else '',
            'at': service['atd'] if 'atd' in service else '',
        }]
        
        if len(service['subsequentCallingPoints']):
            if service['serviceType'] != service['subsequentCallingPoints']['callingPointList'][0]['_serviceType']:
                calling_points[-1]['service_change'] = ugettext_lazy(service['subsequentCallingPoints']['callingPointList'][0]['_serviceType'])
        
        if len(service['previousCallingPoints']):
            if service['serviceType'] != service['previousCallingPoints']['callingPointList'][0]['_serviceType']:
                calling_points[-1]['service_change'] = ugettext_lazy(service['serviceType'])
        
        # Now add services going forward
        if len(service['subsequentCallingPoints']):
            calling_points += service['subsequentCallingPoints']['callingPointList'][0]['callingPoint']
        
        # And do the same with splitting services
        if len(service['subsequentCallingPoints']):
            for i, points in enumerate(service['subsequentCallingPoints']['callingPointList'][1:]):
                # Now we have to handle changes between trains and rail replacement services
                if service['subsequentCallingPoints']['callingPointList'][i]['callingPoint'][-1]['crs'] == points['callingPoint'][0]['crs']:
                    calling_points += points['callingPoint']
                    points['callingPoint'][0]['service_change'] = ugettext_lazy(points['_serviceType'])
                else:
                    for point in calling_points:
                        if points['callingPoint'][0]['crs'] == point['crs']:
                            point['splitting'] = {'destination': points['callingPoint'][-1]['locationName'], 'list': points['callingPoint']}
            
        sources = [calling_points[0]['locationName']]
        for point in calling_points:
            if 'joining' in point:
                sources.append(point['joining'][0]['locationName'])
        
        destinations = [calling_points[-1]['locationName']]
        for point in calling_points:
            if 'splitting' in point:
                destinations.append(point['splitting']['destination'])
        
        stop_entities = []
        
        # Now get a list of the entities for the stations (if they exist)
        # to plot on a map
        for point in calling_points:
        
            if 'joining' in point:
                for jpoint in point['joining']:
                    point_entity = Entity.objects.filter(_identifiers__scheme='crs', _identifiers__value=str(jpoint['crs']))
                    if len(point_entity):
                        point_entity = point_entity[0]
                        jpoint['entity'] = point_entity
                        stop_entities.append(point_entity)
                        jpoint['stop_num'] = len(stop_entities)

            point_entity = Entity.objects.filter(_identifiers__scheme='crs', _identifiers__value=str(point['crs']))
            if len(point_entity):
                point_entity = point_entity[0]
                point['entity'] = point_entity
                stop_entities.append(point_entity)
                point['stop_num'] = len(stop_entities)

            if 'splitting' in point:
                for spoint in point['splitting']['list']:
                    point_entity = Entity.objects.filter(_identifiers__scheme='crs', _identifiers__value=str(spoint['crs']))
                    if len(point_entity):
                        point_entity = point_entity[0]
                        spoint['entity'] = point_entity
                        stop_entities.append(point_entity)
                        spoint['stop_num'] = len(stop_entities)
        
        if 'std' in service:
            title = service['std'] + ' ' + service['locationName'] + ' to ' + ' and '.join(destinations)
        else:
            # This service arrives here
            title = service['sta'] + ' from ' + ' and '.join(sources)
        
        messages = []
        
        if 'disruptionReason' in service:
            messages.append(service['disruptionReason'])
        
        if 'overdueMessage' in service:
            messages.append(service['overdueMessage'])
        
        return {
            'title': title,
            'entities': stop_entities,
            'ldb': service,
            'calling_points': calling_points,
            'has_timetable': True,
            'has_realtime': True,
            'operator': service['operator'],
            'platform': service['platform'],
            'messages': messages
        }
    
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