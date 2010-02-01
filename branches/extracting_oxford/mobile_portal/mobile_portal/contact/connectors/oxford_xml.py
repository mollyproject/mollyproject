from django import forms

from base import BaseContactConnector, ServiceUnavailableException

class OxfordContactForm(forms.Form):
    name = forms.TextField()

class OxfordContactConnector(BaseContactConnector):
    # See http://en.wikipedia.org/wiki/Nobility_particle for more information.
    NOBILITY_PARTICLES = set([
        'de', 'van der', 'te', 'von', 'van', 'du', 'di'
    ])
    
    search_form = OxfordContactForm
    
    def __init__(self, exact=True):
        self.exact = exact
    
    def parse_name(self, name):
        # Examples of initial / surname splitting
        # William Bloggs is W, Bloggs
        # Bloggs         is  , Bloggs
        # W Bloggs       is W, Bloggs
        # Bloggs W       is W, Bloggs
        # Bloggs William is B, William
        parts = name.split(' ')
        parts = [p for p in parts if p]
        i = 0

        while i < len(parts)-1:
            if parts[i].lower() in self.NOBILITY_PARTICLES:
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
            
        return surname, intial
    
class OxfordXMLContactConnector(OxfordContactConnector):
    def search(self, sessionkey, cleaned_data):
        surname, initial = self.parse_name(cleaned_data['name'])
        
        query_string = ';'.join('%s=%s' % i for i in (
            ('surname', re.sub(r"[^A-Za-z\-']", '', surname)),
            ('initial',re.sub(r"[^A-Za-z\-']", '', initial or '')),
            ('match', 'exact' if self.exact else 'approximate'),
            ('type', cleaned_data['medium']),
        ))
        
        try:
            response = urllib2.urlopen(
                CONTACT_SEARCH_URL % query_string,
            )
        except:
            raise ServiceUnavailableException()
            
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