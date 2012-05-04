from molly.conf.provider import Provider
from molly.apps.contact.forms import GenericContactForm
from django.utils.translation import ugettext as _

class BaseContactProvider(Provider):

    class NoSuchResult(KeyError):
        pass

    @property
    def medium_choices(self):
        """
        An attribute consisting of a list of tuples of the media supported by
        this provider (e.g., phonebook, e-mail address list, etc), where the
        tuple is the form ('key', 'description'). The key is what is passed as
        the medium on the ``normalize_query`` method, and the description is
        what is shown to the user.
        """
        return (('all', _('Search')), )

    @property
    def form(self):
        """
        A class object inheriting :class:`~django.forms.Form` to be presented to
        the user and used for input validation. If not overriden, defaults to
        :class:`~molly.apps.contact.forms.GenericContactForm`, which presents a
        single query field.
        """
        return GenericContactForm

    def normalize_query(self, cleaned_data, medium):
        """
        An attribute consisting of a list of tuples of the media supported by
        this provider (e.g., phonebook, e-mail address list, etc), where the
        tuple is the form ('key', 'description'). The key is what is passed as
        the medium on the ``normalize_query`` method, and the description is
        what is shown to the user.
        """
        raise NotImplementedError

    def perform_query(self, **kwargs):
        """
        This method performs a contact lookup based on :data:`**kwargs`.
  
        Each result must be a dictionary containing some subset of the following
        keys (taken from :rfc:`4519` which defines standard LDAP attributes):
  
        * `cn` (common name)
        * `givenName`
        * `sn` (surname)
        * `telephoneNumber`
        * `facsimileTelephoneNumber`
        * `mail` (e-mail addresses)
        * `roomNumber`
        * `title` (job role, etc.)
        * `ou` (organisational unit, e.g. department)
  
        With the exception of `cn`, all should be lists.
  
        Additionally, a result may contain an `id` item, containing a unique
        identifier which may be passed to :meth:`fetch_result`. `id`\ s must be
        URI-safe and not contain forward slashes.
        
        This can return :class:`molly.apps.contact.providers.TooManyResults` if
        the provider (or underlying services) deems that the query has returned
        "too many results"
        """
        raise NotImplementedError

    def fetch_result(self, id):
        """
        May optionally be defined to return the full record for a person, where
        it is decided that :meth:`perform_query` should return a subset of the
        available fields.
  
        If defined, the default results template will provide a link to a page
        for the individual.
        
        If the ID is invalid, self.NoSuchResult is raised
        """
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
