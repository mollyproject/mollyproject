from datetime import date

from mockito import *

from django.test.client import Client
from django.utils import unittest

from molly.apps.places.models import Entity, Journey
from molly.apps.places.providers.cif import CifTimetableProvider

import httplib

class AtcoCifTestCase(unittest.TestCase):
    
    def testBankHolidays(self):
        j = Journey()
        
        # 10 bank hols in 2010
        hols = j.get_bank_holidays(2010)
        self.assertEquals(len(hols), 10)
        self.assertTrue(date(2010, 1, 1) in hols) # New Year's Day
        self.assertTrue(date(2010, 4, 2) in hols) # Good Friday
        self.assertTrue(date(2010, 4, 5) in hols) # Easter Monday
        self.assertTrue(date(2010, 5, 3) in hols) # Early May Bank Holiday
        self.assertTrue(date(2010, 5, 31) in hols) # Spring Bank Holiday
        self.assertTrue(date(2010, 8, 30) in hols) # Summer Bank Holiday
        self.assertTrue(date(2010, 12, 25) in hols) # Christmas Day
        self.assertTrue(date(2010, 12, 26) in hols) # Boxing Day
        self.assertTrue(date(2010, 12, 27) in hols) # Christmas Day (in lieu)
        self.assertTrue(date(2010, 12, 28) in hols) # Boxing Day (in lieu)
        
        # 11 bank hols in 2011
        hols = j.get_bank_holidays(2011)
        self.assertEquals(len(hols), 11)
        self.assertTrue(date(2011, 1, 1) in hols) # New Year's Day
        self.assertTrue(date(2011, 1, 3) in hols) # New Year's Day (in lieu)
        self.assertTrue(date(2011, 4, 22) in hols) # Good Friday
        self.assertTrue(date(2011, 4, 25) in hols) # Easter Monday
        self.assertTrue(date(2011, 4, 29) in hols) # Royal Wedding
        self.assertTrue(date(2011, 5, 2) in hols) # Early May Bank Holiday
        self.assertTrue(date(2011, 5, 30) in hols) # Spring Bank Holiday
        self.assertTrue(date(2011, 8, 29) in hols) # Summer Bank Holiday
        self.assertTrue(date(2011, 12, 25) in hols) # Christmas Day
        self.assertTrue(date(2011, 12, 26) in hols) # Christmas Day (in lieu)
        self.assertTrue(date(2011, 12, 27) in hols) # Boxing Day
        
        # 10 bank hols in 2012
        hols = j.get_bank_holidays(2012)
        self.assertEquals(len(hols), 10)
        self.assertTrue(date(2012, 1, 1) in hols) # New Year's Day
        self.assertTrue(date(2012, 1, 2) in hols) # New Year's Day (in lieu)
        self.assertTrue(date(2012, 4, 6) in hols) # Good Friday
        self.assertTrue(date(2012, 4, 9) in hols) # Easter Monday
        self.assertTrue(date(2012, 5, 7) in hols) # Early May Bank Holiday
        self.assertTrue(date(2012, 6, 4) in hols) # Spring Bank Holiday
        self.assertTrue(date(2012, 6, 5) in hols) # Diamond Jubilee
        self.assertTrue(date(2012, 8, 27) in hols) # Summer Bank Holiday
        self.assertTrue(date(2012, 12, 25) in hols) # Christmas Day
        self.assertTrue(date(2012, 12, 26) in hols) # Boxing Day

class LocationTestCase(unittest.TestCase):
    def testLocationRequiredViewSubclass(self):
        c = Client()
        path = '/places/nearby/'
        latitude = 51.752274
        longitude = -1.255875
        accuracy = 10
        
        # Trying to get a LocationRequiredView with no location set should
        # cause a redirect
        response = c.get(path)
        self.assertEquals(response.status_code, httplib.SEE_OTHER)
        
        # Trying to get a LocationRequiredView with latitude and longitude
        # query params returns OK
        response = c.get(path, data={ 'latitude':latitude, 'longitude': longitude })
        self.assertEquals(response.status_code, httplib.OK)
        
        # Trying to get a LocationRequiredView with latitude, longitude
        # and accuracy query params returns OK
        response = c.get(path, data={ 'latitude':latitude, 'longitude': longitude, 'accuracy': accuracy })
        self.assertEquals(response.status_code, httplib.OK)

        # Trying to get a LocationRequiredView with an X-Current-Location (no accuracy)
        # HTTP header returns OK
        response = c.get(path, HTTP_X_CURRENT_LOCATION="latitude=%.6f,longitude=%.6f" % (latitude, longitude))
        self.assertEquals(response.status_code, httplib.OK)

        # Trying to get a LocationRequiredView with an X-Current-Location (including accuracy)
        # HTTP header returns OK
        response = c.get(path, HTTP_X_CURRENT_LOCATION="latitude=%.6f,longitude=%.6f,accuracy=%d" % (latitude, longitude, accuracy))
        self.assertEquals(response.status_code, httplib.OK)


class CifTestCase(unittest.TestCase):
    
    sample_file = \
"""
HDTPS.UCFCATE.PD1201131301122139DFTTISX       FA130112300912                    
TIAACHEN 00081601LAACHEN                    00005   0                           
TIABCWM  00385964VABERCWMBOI                78128   0
"""
    
    class MockQuerySet():
        
        def __init__(self, mockObj):
            self._mock = mockObj
        
        def count(self):
            return 1
        
        def __getitem__(self, index):
            return self._mock
    
    def setUp(self):
        self.mock_entity_manager = mock()
        self.provider = CifTimetableProvider(
            entity_manager=self.mock_entity_manager
        )
        
        self.empty_query_set = mock()
        self.entity_query_set = self.MockQuerySet(mock())
        when(self.empty_query_set).count().thenReturn(0)
        when(self.mock_entity_manager).get_entity(
            'tiploc', 'ABCWM').thenReturn(self.empty_query_set)
        when(self.mock_entity_manager).get_entity(
            "tiploc", 'AACHEN').thenReturn(self.entity_query_set)
    
    def testThatTiplocsAreLookedUp(self):
        self.provider.import_from_string(self.sample_file)
        verify(self.mock_entity_manager, times=2).get_entity(any(), any())
    
    def testThatTiplocsAreLookedUpWithCorrectNamespace(self):
        self.provider.import_from_string(self.sample_file)
        verify(self.mock_entity_manager, times=2).get_entity("tiploc", any())
    
    def testThatTiplocsAreLookedUpWithName(self):
        self.provider.import_from_string(self.sample_file)
        verify(self.mock_entity_manager).get_entity("tiploc", "AACHEN")
    
    def testThatTiplocsAreLookedUpWithStrippedName(self):
        self.provider.import_from_string(self.sample_file)
        verify(self.mock_entity_manager).get_entity('tiploc', 'ABCWM')
    
    def testThatTiplocsAreCreatedWhenNoneAreReturned(self):
        self.provider.import_from_string(self.sample_file)
        
        # Annoyingly mockito doesn't properly support assertions on the args
        verify(self.mock_entity_manager).create(
            source=any(),
            primary_type=any(),
            identifiers=any(),
            titles=any()
        )
    
    def testThatTiplocsAreCreatedWithCorrectSource(self):
        self.provider = CifTimetableProvider()
        self.provider.import_from_string(self.sample_file)
        entity = Entity.objects.get_entity('tiploc', 'ABCWM')
        self.assertEquals(self.provider.source, entity[0].source)
    
    def testThatTiplocsAreCreatedWithCorrectType(self):
        self.provider = CifTimetableProvider()
        self.provider.import_from_string(self.sample_file)
        entity = Entity.objects.get_entity('tiploc', 'ABCWM')
        self.assertEquals(self.provider.entity_type, entity[0].primary_type)
    
    def testThatTiplocsAreCreatedWithCorrectName(self):
        self.provider = CifTimetableProvider()
        self.provider.import_from_string(self.sample_file)
        entity = Entity.objects.get_entity('tiploc', 'ABCWM')
        self.assertEquals('Abercwmboi', entity[0].title)
    
    def testGetSource(self):
        self.assertEquals(
            'molly.apps.places.providers.cif',
            self.provider.source.module_name
        )
    
    def testGetEntityTypeVerboseName(self):
        self.assertEquals(
            'rail network timing point',
            self.provider.entity_type.verbose_name
        )
    
    def testGetEntityTypeVerboseNamePlural(self):
        self.assertEquals(
            'rail network timing points',
            self.provider.entity_type.verbose_name_plural
        )
    
    def testGetEntityTypeVerboseNameSingular(self):
        self.assertEquals(
            'a rail network timing point',
            self.provider.entity_type.verbose_name_singular
        )


if __name__ == '__main__':
    unittest.main()
