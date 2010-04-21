import urllib, re, logging

import simplejson

from molly.geolocation.providers import BaseGeolocationProvider

logger = logging.getLogger('molly.contrib.oxford.providers.geolocation')

class OUCSCodeGeolocationProvider(BaseGeolocationProvider):

    OXPOINTS_OUCSCODE_URL = 'http://oxpoints.oucs.ox.ac.uk/oucs:%s.json'
    OUCSCODE_RE = re.compile(r'^[a-z]+$')

    
    def geocode(self, query):
        query = query.lower()
        if self.OUCSCODE_RE.match(query):
            try:
                response = urllib.urlopen(self.OXPOINTS_OUCSCODE_URL % query)
                if response.code != 200:
                    logger.error("OUCS code geolocation look-up for '%s' returned code %d." % (query, response.code))
                    return []
            except Exception, e:
                logger.exception("OUCS code geolocation look-up for '%s' failed." % query)
                return []
            
            try:
                results = simplejson.load(response)
                return [{
                    'name': result['dc_title'],
                    'location': (result['geo_long'], result['geo_lat']),
                    'accuracy': 100,
                } for result in results]
            except Exception, e:
                logger.exception("OUCS code geolocation look-up for '%s' not in expected format." % query)
                return []
        return []