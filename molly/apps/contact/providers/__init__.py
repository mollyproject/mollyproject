from molly.apps.contact.forms import GenericContactForm

class BaseContactProvider(object):

    class NoSuchResult(KeyError):
        pass

    @property
    def handles_pagination(self):
        raise NotImplementedError

    @property
    def medium_choices(self):
        return (('all', 'Search'), )

    @property
    def form(self):
        return GenericContactForm

    def normalize_query(self, cleaned_data):
        raise NotImplementedError

    def perform_query(self, data=None, **kwargs):
        raise NotImplementedError

    def fetch_result(self, id):
        raise BaseContactProvider.NoSuchResult

class TooManyResults(Exception):
    pass

try:
    import ldap
except ImportError:
    pass
else:
    del ldap
    from mit import LDAPContactProvider