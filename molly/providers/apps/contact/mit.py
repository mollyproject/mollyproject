import ldap, ldap.filter

from molly.apps.contact.providers import BaseContactProvider

class LDAPContactProvider(BaseContactProvider):
    """
    Connects to MIT's LDAP server to request contact information.
    """

    # See http://en.wikipedia.org/wiki/Nobility_particle for more information.
    _NOBILITY_PARTICLES = set([
        'de', 'van der', 'te', 'von', 'van', 'du', 'di'
    ])

    # URL for the contact search API. Speak to sysdev for access.
    _LDAP_URL = 'ldap://ldap.mit.edu:389'
    _BASE_DN = "dc=mit,dc=edu"

    handles_pagination = False

    @classmethod
    def normalize_query(cls, cleaned_data, medium):
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
            surname, forename = parts[0], None
        elif parts[0].endswith(','):
            surname, forename = parts[0][:-1], parts[1]
        else:
            surname, initial = parts[1], parts[0]

        return {
            'surname': surname,
            'forename': forename,
        }

    @classmethod
    def first_or_none(cls, result, name):
        try:
            return result[1][name][0]
        except (KeyError, IndexError):
            return None

    @classmethod
    def perform_query(cls, surname, forename):

        mitldap = ldap.initialize(cls._LDAP_URL)
        ldap_results = mitldap.search_ext_s(cls._BASE_DN, ldap.SCOPE_SUBTREE, "(sn=%s)" % 
            ldap.filter.escape_filter_chars(surname),
        )

        results = []
        for ldap_result in ldap_results:
            results.append({
                'cn': cls.first_or_none(ldap_result, 'cn'),

                'sn': ldap_result[1].get('sn', []),
                'givenName': ldap_result[1].get('givenName', []),
                'telephoneNumber': ldap_result[1].get('telephoneNumber', []),
                'roomNumber': ldap_result[1].get('roomNumber', []),
                'title': ldap_result[1].get('title', []),
                'facsimileTelephoneNumber': ldap_result[1].get('facsimileTelephoneNumber', []),
                'ou': ldap_result[1].get('ou', []),
                'mail': ldap_result[1].get('mail', []),
            })

        return results

