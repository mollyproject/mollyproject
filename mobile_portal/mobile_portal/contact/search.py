from xml.etree import ElementTree as ET
import ElementSoup as ES
import urllib, urllib2

CONTACT_SEARCH_URL = 'http://www.ox.ac.uk/applications/contact_search/index.rm?%s'

def contact_search(surname, initial, exact, medium, page=1):
    """
    Screenscrapes contact details from the main University contact search page and returns
    a list of dictionaries containing contact information.
    """
    
    query_string = urllib.urlencode({
        'lastname':surname,
        'initial':initial or '',
        'exact': 'true' if exact else 'false',
        'find_%s' % medium: '',
        'page': page
    })
    response = urllib2.urlopen(
        CONTACT_SEARCH_URL % query_string,
    )
    xml = ES.parse(response)
    try:
        x_people = filter(lambda x:(x.attrib.get('class')=='people'), xml.findall('.//ul'))[0]
    except IndexError:
        # No people found
        return [], 0

    people = []
    for x_person in x_people.getchildren():
        details = {}
        for x_detail in x_person.getchildren():
            if x_detail.attrib['class'].split('_')[1] == 'phone':
                details[u'phone'] = (x_detail[0][1].text, x_detail[0][3].text)
            else:
                details[x_detail.attrib['class'].split('_')[1]] = x_detail.text.strip() or x_detail[0].text
        people.append( details )

    page_count = int(filter(lambda x:(x.attrib.get('class')=='found'), xml.findall('.//div'))[0][1][4].text)

    return people, page_count

