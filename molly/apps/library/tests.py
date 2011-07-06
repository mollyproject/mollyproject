import urllib

from django.utils import unittest
from django.test import TestCase
from django.conf import settings
from django.core.management import call_command

from PyZ3950 import z3950 as z3950_
from PyZ3950 import zoom

from molly.apps.library.models import LibrarySearchQuery
from molly.apps.library.providers import z3950

TEST_DATA = [
"00927nam  2200301 a 4500001001500000003000600015005001700021008004100038010001700079015001900096016001800115020002500133020002200158035002300180035001300203040004900216042001400265050002800279082001500307100003200322245006100354260003300415300003500448500002000483650001800503700001500521852008900536\x1eUkOxUb16686899\x1eUkOxU\x1e20080430135602.0\x1e071012s2007    cc a          001 0 eng d\x1e  \x1fa  2007278140\x1e  \x1faGBA709991\x1f2bnb\x1e7 \x1fa013660805\x1f2Uk\x1e  \x1fa9780596529260 (pbk.)\x1e  \x1fa0596529260 (pbk.)\x1e  \x1fa(OCoLC)ocm82671871\x1e  \x1fa15042568\x1e  \x1faUKM\x1fcUKM\x1fdBAKER\x1fdBTCTA\x1fdYDXCP\x1fdDPL\x1fdIXA\x1fdDLC\x1e  \x1falccopycat\x1e00\x1faTK5105.88813\x1fb.R53 2007\x1e04\x1fa006.76\x1f222\x1e1 \x1faRichardson, Leonard,\x1fd1979-\x1e10\x1faRESTful web services /\x1fcLeonard Richardson and Sam Ruby.\x1e  \x1faFarnham :\x1fbO'Reilly,\x1fcc2007.\x1e  \x1faxxiv, 419 p. :\x1fbill. ;\x1fc24 cm.\x1e  \x1faIncludes index.\x1e 0\x1faWeb services.\x1e1 \x1faRuby, Sam.\x1e  \x1faUkOxU\x1fbRadcl.Science\x1fbRSL Level 2\x1fhTK 5105.88813 RIC\x1f720689922\x1fp306162820\x1fyReference\x1e\x1d",
'01567nam  2200361 a 45M0001001500000003000600015005001700021008004100038010001500079020001500094024001900109035002700128050002200155082001400177092001600191100001700207245007700224250001100301260005700312300003200369440004600401504002900447504001900476650001500495650002500510971000800535852008500543852009000628852013700718852011100855852011100966852012801077\x1eUkOxUb10017358\x1eUkOxU\x1e20000224140527.0\x1e890215s1988    maua      b   001 0 eng d\x1e  \x1falc87009205\x1e  \x1fa0201060353\x1e2 \x1fa19372295\x1fc+LCX\x1e  \x1faCURL 05lc87009205(Lon)\x1e 0\x1faQA76.6\x1fb.B25 1988\x1e  \x1fa519.7\x1f219\x1e  \x1faD0400017640\x1e1 \x1faBaase, Sara.\x1e10\x1faComputer algorithms :\x1fbintroduction to design and analysis /\x1fcSara Baase\x1e  \x1fa2nd ed\x1e  \x1faReading, Mass ;\x1faWokingham :\x1fbAddison-Wesley,\x1fcc1988\x1e  \x1faxv, 415 p. :\x1fbill. ;\x1fc25 cm\x1e 0\x1faAddison-Wesley series in computer science\x1e  \x1faBibliography: p. 397-403\x1e  \x1faIncludes index\x1e 0\x1faAlgorithms\x1e 0\x1faComputer programming\x1e  \x1facmw\x1e  \x1faUkOxU\x1fbEngineering\x1fbENG Main Libr\x1fhPT2.baa\x1f712749035\x1fp302102211\x1fyCheck the Shelf\x1e  \x1faUkOxU\x1fbPembroke Coll\x1fbPEM Main Libr\x1fhM 9.4 BAA\x1f712749034\x1fp302890267\x1fx91193\x1fyAvailable\x1e  \x1faUkOxU\x1fbRadcl.Science\x1fbRSL Offsite\x1fh00.E05482\x1f712749033\x1fm(Box B000001063108)\x1fp300206976\x1fyIn place\x1fzformerly at Comp. Cj 10\x1f5300206976\x1e  \x1faUkOxU\x1fbWadham Coll.\x1fbWAD Main Libr\x1fhM 40 (B)\x1f712749030\x1fm2nd copy\x1fp303455625\x1fx1989/856\x1fy\x1fzBNA 33943M \xb926.78\x1e  \x1faUkOxU\x1fbWadham Coll.\x1fbWAD Main Libr\x1fhM 40 (B)\x1f712749031\x1fm1st copy\x1fp303455624\x1fx1989/855\x1fy\x1fzBNA 33943M \xb926.78\x1e  \x1faUkOxU\x1fbWadham Coll.\x1fbWAD Main Libr\x1fhM 40 (B)\x1f712749032\x1fmThird copy\x1fp300606910\x1fx1992/717\x1fxGift of Dr W McColl October 1992\x1fy\x1e\x1d',
]

TEST_METADATA = [
    {
#        'author': '',
        'title': 'RESTful web services / Leonard Richardson and Sam Ruby.',
        'publisher': "Farnham : O'Reilly, c2007.",
        'description': 'xxiv, 419 p. : ill. ; 24 cm.',
    },
    {
        'title': 'Computer algorithms : introduction to design and analysis / Sara Baase',
        'publisher': "Reading, Mass ; Wokingham : Addison-Wesley, c1988",
        'description': 'xv, 415 p. : ill. ; 25 cm',
    },
]

class FakeOLISResult(z3950.USMARCSearchResult):
    def __init__(self, data):
        db_name = 'MAIN*BIBMAST'
        super(FakeOLISResult, self).__init__(
            zoom.Record(
                z3950_.Z3950_RECSYN_USMARC_ov, data, db_name
        ))

class USMARCTestCase(TestCase):

    def testGetDetails(self):
        for data, metadata in zip(TEST_DATA, TEST_METADATA):
            result = FakeOLISResult(data)
            for k in metadata:
                self.assertEqual(getattr(result, k), metadata[k])


TEST_ISBNS = [
    '1903402557', '0134841891', '0262041677', '0340811293', '1565925858',
]
               
TEST_AUTHORS = [
    'Adolf Hitler', 'Peter F Hamilton', 'Rushdie', 'Jeremy Clarkson', 'Gandhi',
    'Jeremy Black', 'Stewart III',
]

TEST_HOST = 'library.ox.ac.uk'
TEST_DATABASE = 'MAIN*BIBMAST'

class SearchTestCase(TestCase):
    
    def testAuthorSearch(self):
        
        for author in TEST_AUTHORS:
            response = self.client.get('/library/search/?%s' % urllib.urlencode({
                'author': author,
                'title': '',
                'isbn': '',
            }))
            self.assertEqual(response.status_code, 200)
            
    def testOLISSearch(self):
        for author in TEST_AUTHORS:
            q = LibrarySearchQuery(author=author)
            results = z3950.Z3950(TEST_HOST, TEST_DATABASE).library_search(q)
            self.assert_(len(results) > 0)

    def testISBNSearch(self):
        for isbn in TEST_ISBNS:
            q = LibrarySearchQuery(isbn=isbn)
            results = z3950.Z3950(TEST_HOST, TEST_DATABASE).library_search(q)
            self.assert_(len(results) > 0, "No results for ISBN %s" % isbn)
    
