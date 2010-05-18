import urllib, urllib2
from lxml import etree

from molly.apps.contact.providers import BaseContactProvider


class BrookesContactProvider(BaseContactProvider):

    _API_URL = 'http://owww.brookes.ac.uk/cgi-bin/cs/webldap/webldap.cgi'

    handles_pagination = False

    def normalize_query(self, cleaned_data, medium):
        return {
            'query': cleaned_data['query'],
        }

    def perform_query(self, query):
        request = urllib2.Request(self._API_URL)
        request.add_header('Referer', 'http://www.brookes.ac.uk/externalsearch')
        request.add_data(urllib.urlencode([
                ('searchattr', 'cn'),
                ('query', query),
                ('flags', 'btable,nodn'),
                ('attr', 'cn'),
                ('attr', 'mail'),
                ('attr', 'description'),
                ('attr', 'ou'),
                ('attr', 'telephoneNumber'),
                ('attr', 'roomNumber'),
                ('objectclass', 'inetOrgPerson'),
                ('match', '%%a=*%%v*'),
                ('flags', 'valsonly'),
                ('flags', 'entryonly'),
            ]))

        response = urllib2.urlopen(request)
        xml = etree.parse(response, parser=etree.HTMLParser())

        people = []
        for person in xml.findall('.//tr')[1:]:
            details = {
                'cn': person[0].text,
                'mail': [person[1].text or ''],
                'title': [person[2].text or ''],
                'ou': [person[3].text or ''],
                'telephoneNumber': [person[4].text or ''],
            }

            people.append( details )

        return people

