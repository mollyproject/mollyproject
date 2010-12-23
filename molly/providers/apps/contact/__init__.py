try:
    import ldap
except ImportError:
    pass
else:
    del ldap
    from mit import LDAPContactProvider

from oxford import ContactProvider, ScrapingContactProvider
