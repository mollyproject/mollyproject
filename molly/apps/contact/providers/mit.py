from operator import itemgetter

import ldap
import ldap.filter

from molly.apps.contact.providers import BaseContactProvider, TooManyResults

class LDAPContactProvider(BaseContactProvider):
    
    # See http://en.wikipedia.org/wiki/Nobility_particle for more information.
    _NOBILITY_PARTICLES = set([
        'de', 'van der', 'te', 'von', 'van', 'du', 'di'
    ])
    
    def __init__(self, url, base_dn, phone_prefix='', phone_formatter=None,
                 alphabetical=False, query='(sn={surname})'):
        self._url = url
        self._base_dn = base_dn
        if phone_formatter is None:
            phone_formatter = lambda t: '%s%s' % (phone_prefix, t)
        self._phone_formatter = phone_formatter
        self.alphabetical = alphabetical
        self.query = query
    
    def normalize_query(self, cleaned_data, medium):
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
            if parts[i].lower() in self._NOBILITY_PARTICLES:
                parts[i:i+2] = [' '.join(parts[i:i+2])]
            elif parts[i] == '':
                parts[i:i+1] = []
            else:
                i += 1
        
        parts = parts[:2]
        if len(parts) == 1:
            surname, forename = parts[0], None
        elif parts[0].endswith(','):
            surname, forename = parts[0][:-1], parts[1]
        else:
            surname, forename = parts[1], parts[0]
        
        return {
            'surname': surname,
            'forename': forename,
        }

    def first_or_none(self, result, name):
        try:
            return result[1][name][0]
        except (KeyError, IndexError):
            return None

    def perform_query(self, surname, forename):
        
        ldap_server = ldap.initialize(self._url)
        
        if forename is None:
            forename = ''
        
        try:
            ldap_results = ldap_server.search_ext_s(
                self._base_dn, ldap.SCOPE_SUBTREE,
                self.query.format(
                    surname=ldap.filter.escape_filter_chars(surname),
                    forename=ldap.filter.escape_filter_chars(forename))
            )
        except ldap.NO_SUCH_OBJECT:
            return []
        except ldap.SIZELIMIT_EXCEEDED:
            raise TooManyResults()
        
        results = []
        for ldap_result in ldap_results:
            results.append({
                'cn': self.first_or_none(ldap_result, 'cn'),
                'sn': ldap_result[1].get('sn', []),
                'givenName': ldap_result[1].get('givenName', []),
                'telephoneNumber': map(self._phone_formatter,ldap_result[1].get('telephoneNumber', [])),
                'roomNumber': ldap_result[1].get('roomNumber', []),
                'title': ldap_result[1].get('title', []),
                'facsimileTelephoneNumber': ldap_result[1].get('facsimileTelephoneNumber', []),
                'ou': ldap_result[1].get('ou', []),
                'mail': ldap_result[1].get('mail', []),
            })
        
        if self.alphabetical:
            return sorted(results, key=itemgetter('sn', 'givenName'))
        else:
            return results
