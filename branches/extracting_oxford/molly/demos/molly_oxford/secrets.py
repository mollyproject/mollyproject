class _Secrets(dict):
    def __getattr__(self, key):
        return self[key]

SECRETS = _Secrets({
    'database_name': 'molly',
    'database_user': 'molly',
    'database_password': 'molly',
    'database_host': '',
    'secret_key': 'secret key',

    'weblearn': (None, None),
    'cloudmade': None,
    'google': None,
    'yahoo': None,
    'fireeagle': None,
})
