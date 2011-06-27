from datetime import date

from django.utils import unittest

from molly.apps.places.models import Journey

class AtcoCifTestCase(unittest.TestCase):
    
    def testBankHolidaysNormal(self):
        j = Journey()
        
        # 10 bank hols in 2010
        hols = p.get_bank_holidays(2010)
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
        
        # 12 bank hols in 2011
        hols = p.get_bank_holidays(2011)
        self.assertEquals(len(hols), 12)
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
        
        # 11 bank hols in 2012
        hols = p.get_bank_holidays(2012)
        self.assertEquals(len(hols), 11)
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

if __name__ == '__main__':
    unittest.main()
