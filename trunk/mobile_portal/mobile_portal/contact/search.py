from xml.etree import ElementTree as ET
import urllib, urllib2, re

CONTACT_SEARCH_URL = 'http://www2.ox.ac.uk/cgi-bin/contactx?%s'

def contact_search(surname, initial, exact, medium):
    """
    Screenscrapes contact details from the main University contact search page and returns
    a list of dictionaries containing contact information.
    """
    
    query_string = ';'.join('%s=%s' % i for i in (
        ('surname', re.sub(r"[^A-Za-z\-']", '', surname)),
        ('initial',re.sub(r"[^A-Za-z\-']", '', initial or '')),
        ('match', 'exact' if exact else 'approximate'),
        ('type', medium),
    ))
    response = urllib2.urlopen(
        CONTACT_SEARCH_URL % query_string,
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
