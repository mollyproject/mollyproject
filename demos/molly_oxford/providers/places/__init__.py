import urllib2, logging
from lxml import etree
from django.conf import settings

from molly.apps.places.providers import BaseMapsProvider

logger = logging.getLogger("molly_oxford.providers.apps.places.park_and_ride")

class OxfordParkAndRidePlacesProvider(BaseMapsProvider):
    _VOYAGER_URL = "http://voyager.oxfordshire.gov.uk/Carpark.aspx"
    
    _CARPARKS = {
        'Pear Tree Park & Ride OX2 8JD': "W4333225",
        'Redbridge Park & Ride OX1 4XG': "W2809915",
        'Seacourt Park & Ride OX2 0HP': "W34425625",
        'Thornhill Park & Ride OX3 8DP': "W24719725",
        'Water Eaton Park & Ride OX2 8HA': "W4329908",
    }
    _CARPARK_IDS = _CARPARKS.values()

    def augment_metadata(self, entities):
        carparks = {}

        for entity in entities:
            if entity.identifiers.get('osm') in self._CARPARK_IDS:
                carparks[entity.identifiers['osm']] = entity

        if not carparks:
            return

        try:
            xml = etree.parse(urllib2.urlopen(self._VOYAGER_URL), parser = etree.HTMLParser())
            tbody = xml.find(".//div[@class='cloud-amber']/table/tbody")

            for tr in tbody:
                name = tr[1].text.strip()

                if not name in self._CARPARKS:
                    logger.warning("A new car park has appeared with name %r" % name)
                    continue
                    
                if not self._CARPARKS[name] in carparks:
                    continue
                
                unavailable = False
                try:
                    spaces = int(tr[2].text)
                except ValueError:
                    spaces = 0
                    unavailable = True

                carparks[self._CARPARKS[name]].metadata['park_and_ride'] = {
                    'spaces': spaces,
                    'capacity': int(tr[3].text),
                    'percentage': int(100 * (1 - float(spaces) / float(tr[3].text))),
                    'unavailable': unavailable,
                }
        except Exception, e:
            if settings.DEBUG: raise
            logger.exception("The Park and Ride page has changed in some way")
            for name in self._CARPARKS:
                if 'park_and_ride' not in carparks[self._CARPARKS[name]].metadata:
                    carparks[self._CARPARKS[name]].metadata['park_and_ride'] = {
                        'spaces': '?',
                        'capacity': '?',
                        'percentage': 0,
                        'unavailable': True,
                    }
