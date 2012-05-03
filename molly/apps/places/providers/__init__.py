from molly.conf.provider import Provider


class BaseMapsProvider(Provider):
    def import_data(self):
        pass
        
    def real_time_information(self, entity):
        return None
    
    def augment_metadata(self, entities, **kwargs):
        pass

from naptan import NaptanMapsProvider
from acislive import ACISLiveMapsProvider, ACISLiveRouteProvider
from osm import OSMMapsProvider
from postcodes import PostcodesMapsProvider
from ldb import LiveDepartureBoardPlacesProvider
from bbc_tpeg import BBCTPEGPlacesProvider
from tfl import TubeRealtimeProvider
from atcocif import AtcoCifTimetableProvider
from timetables import TimetableAnnotationProvider
