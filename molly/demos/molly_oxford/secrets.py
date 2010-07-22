class _Secrets(dict):
    def __getattr__(self, key):
        return self[key]

# You'll need to override some of these for particular bits of functionality
# to work.

SECRETS = _Secrets({
    'database_name': 'molly',
    'database_user': 'molly',
    'database_password': 'molly',
    'database_host': '',
    'secret_key': 'secret key',

    'weblearn': ('mobileox-dev', 'gatae1reeHai6Oogaequ'),
    'cloudmade': 'a1e6c80b8ea450fcbaa294b673f0e42d',
    'google': None,
    'yahoo': None,
    'fireeagle': None,
    'journeyweb': ('timfernando', 'tamefruit037'),
})
