import unittest, random

from django.core.management import call_command
from django.test.client import Client
from django.core.urlresolvers import reverse

from mobile_portal.core.utils import OXFORD_EMAIL_RE

class AjaxSetLocationTestCase(unittest.TestCase):
    def setUp(self):
        self.client = Client()
        self.test_url = reverse('core_ajax_update_location')
        
    def testGET(self):
        "GET should return a 405 Method Not Acceptable"
        response = self.client.get(self.test_url)
        self.assertEqual(response.status_code, 405)
        
    def testEmptyPOST(self):
        "An empty POST should return a 400 Bad Request"
        response = self.client.post(self.test_url)
        self.assertEqual(response.status_code, 400)
        
    def testLocationRequirements(self):
        "Depending on method, a location should either be required or forbidden."
        
        grouped_methods = {
            True: ('html5', 'gears', 'manual', 'geocoded', 'other'),
            False: ('error', 'denied'),
        }
        
        for require_location, methods in grouped_methods.items():
            for method in methods:
                response = self.client.post(self.test_url, {
                    'method': method,
                    'latitude': 0,
                    'longitude': 0,
                })
                expected_code = require_location and 200 or 400
                self.assertEqual(response.status_code, expected_code)
                
                response = self.client.post(self.test_url, {
                    'method': method,
                })
                expected_code = require_location and 400 or 200
                self.assertEqual(response.status_code, expected_code)
    
    def testAccuracy(self):
        "accuracy implies location"
        
        response = self.client.post(self.test_url, {
            'method': 'other',
            'latitude': 0,
            'longitude': 0,
            'accuracy': 10,
        })
        self.assertEqual(response.status_code, 200)
        
        response = self.client.post(self.test_url, {
            'method': 'other',
            'accuracy': 10,
        })
        self.assertEqual(response.status_code, 400)
        
        

class CoreTestCase(unittest.TestCase):
    def setUp(self):
        self.client = Client()
        
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