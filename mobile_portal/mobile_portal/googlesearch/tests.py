import unittest, sys
from search import GoogleSearch

class GenericSearchTestCase(unittest.TestCase):
    def testOne(self):
        gs = GoogleSearch('m.ox.ac.uk', 'podcasts', 'keble')
        for r in gs:
            print >>sys.__stdout__,r
