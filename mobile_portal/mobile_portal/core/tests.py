import unittest, random

from django.core.management import call_command
from django.test.client import Client
from django.core.urlresolvers import reverse

from mobile_portal.core.utils import OXFORD_EMAIL_RE

class CoreTestCase(unittest.TestCase):
    def setUp(self):
        self.client = Client()
        
    def testSetLocationUsingAjax(self):
        for i in range(10):
            self.client = Client()
            
            latitude, longitude = random.randrange(-120, 120), random.randrange(-210,210)
            valid_input = -90 <= latitude and latitude < 90 and -180 <= longitude and longitude < 180
            
            response = self.client.post('/core/ajax/update_location/', {
                'longitude': longitude,
                'latitude': latitude,
            })
            
            if valid_input:
                self.assertEqual(response.status_code, 200) # OK
            else:
                self.assertEqual(response.status_code, 400) # Bad Request
                
            response = self.client.get('/')
            if valid_input:
                self.assertEqual(response.context['location'], (latitude, longitude))
            else:
                self.assertEqual(response.context['location'], None)
                
    def testSetLocationManually(self):
        test_locations = (
            'Keble College', 'OX26NN', 'Germany', 'Antartica', '51 4',
            '12 Banbury Road, Oxford', 'Paris', 'W1A 1AA', 'dago;gns'
        )
        
        for location in test_locations:
            response = self.client.post('/core/update_location/', {
                'location': location
            })
            
            self.assertTrue(response.status_code in (303, 200), # Found, OK
                "Unexpected status code: %d" % response.status_code)
   
    def testOxfordEmailRegex(self):
        oxford_addresses = (
            'bob.builder@estates.ox.ac.uk',
            'jeremy.kyle@naff-tv.ox.ac.uk',
            'barry.bookworm@oup.com',
            
        )
        non_oxford_addresses = (
            'ingrid.imposter@fake.sox.ox.ac.uk',
            'couch.potato@coup.com',
            'james@hotmail.com',
        )
        
        for address in oxford_addresses:
            self.assert_(OXFORD_EMAIL_RE.match(address),
                "%s didn't match as an Oxford e-mail address when it should." % address)
        for address in non_oxford_addresses:
            self.assert_(not OXFORD_EMAIL_RE.match(address),
                "%s matched as an Oxford e-mail address when it shouldn't." % address)