from xml.etree import ElementTree as ET
import urllib, urllib2, re

from django.core.paginator import Paginator

import ElementSoup as ES

class ContactProvider(object):
    """
    Connects to the University's contact search API on www2.ox.
    Note that the use of this service requires talking to sysdev.
    You may also be interested in the screen-scraped version.
    """

    # See http://en.wikipedia.org/wiki/Nobility_particle for more information.
    _NOBILITY_PARTICLES = set([
        'de', 'van der', 'te', 'von', 'van', 'du', 'di'
    ])

    # URL for the contact search API. Speak to sysdev for access.
    _API_URL = 'http://www2.ox.ac.uk/cgi-bin/contactx?%s'

    @classmethod
    def normalize_query(cls, cleaned_data):
        # Examples of initial / surname splitting
        # William Bloggs is W, Bloggs
        # Bloggs         is  , Bloggs
        # W Bloggs       is W, Bloggs
        # Bloggs W       is W, Bloggs
        # Bloggs William is B, William
        parts = cleaned_data['query'].split(' ')
        parts = [p for p in parts if p]
        i = 0

        while i < len(parts)-1:
            if parts[i].lower() in _NOBILITY_PARTICLES:
                parts[i:i+2] = [' '.join(parts[i:i+2])]
            elif parts[i] == '':
                parts[i:i+1] = []
            else:
                i += 1

        parts = parts[:2]
        if len(parts) == 1:
            surname, initial = parts[0], None
        elif parts[0].endswith(','):
            surname, initial = parts[0][:-1], parts[1][:1]
        elif len(parts[1]) == 1:
            surname, initial = parts[0], parts[1]
        else:
            surname, initial = parts[1], parts[0][:1]

        medium = cleaned_data['medium'] or 'email'

        return {
            'surname': surname,
            'initial': initial,
            'medium': medium,
            'exact': True,
        }

    handles_pagination = False

    @classmethod
    def perform_query(cls, surname, initial, medium, exact):

        query_string = ';'.join('%s=%s' % i for i in (
            ('surname', re.sub(r"[^A-Za-z\-']", '', surname)),
            ('initial',re.sub(r"[^A-Za-z\-']", '', initial or '')),
            ('match', 'exact' if exact else 'approximate'),
            ('type', medium),
        ))
        response = urllib2.urlopen(
            cls._API_URL % query_string,
        )
        x_people = ET.parse(response)

        people = []
        for x_person in x_people.getroot().findall('person'):
            person = {
                'name': x_person.find('name').text,
                'unit': x_person.find('unit' if medium=='email' else 'dept').text,
            }
            if medium == 'email':
                person['email'] = x_person.find('email').text
            else:
                person['internal'] = x_person.find('phone_from_in').text
                person['external'] = x_person.find('phone_from_out').text
            people.append(person)

        return people

class ScrapingContactProvider(ContactProvider):

    _API_URL = 'http://www.ox.ac.uk/applications/contact_search/index.rm?%s'

    handles_pagination = True

    @classmethod
    def perform_query(cls, surname, initial, medium, exact, page):
        query_string = urllib.urlencode({
            'lastname':surname,
            'initial':initial or '',
            'exact': 'true' if exact else 'false',
            'find_%s' % medium: '',
            'page': page
        })
        response = urllib2.urlopen(
            cls._API_URL % query_string,
        )
        xml = ES.parse(response)
        try:
            x_people = filter(lambda x:(x.attrib.get('class')=='people'), xml.findall('.//ul'))[0]
        except IndexError:
            # No people found
            return [], 0, 0

        people = [] 
        for x_person in x_people.getchildren():
            details = {}
            for x_detail in x_person.getchildren():
                if x_detail.attrib['class'].split('_')[1] == 'phone':
                    details[u'internal'] = x_detail[0][1].text
                    details[u'external'] = x_detail[0][3].text
                else:
                    details[x_detail.attrib['class'].split('_')[1]] = x_detail[0].text if len(x_detail) else (x_detail.text.strip() or None)
            people.append( details )

        results_count = int(filter(lambda x:(x.attrib.get('class')=='found'), xml.findall('.//div'))[0][1][0].text)
        
        people = range(0, (page-1)*10) + people
        people += range(0, results_count-len(people))
        return Paginator(people, 10)

