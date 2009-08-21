from datetime import datetime
from preferences import PreferenceSet

EPOCH = datetime(1970,1,2)

DEFAULTS_CHOICES = (
    ('new', 'New user'),
)

defaults = {
    'new': PreferenceSet({
        'location': (EPOCH, {
            'method': None,
            'location': None,
            'placemark': None,
            'accuracy': None,
            'requested': None,
            'updated': None,
        }),
        'front_page_links': (EPOCH, PreferenceSet({
            'contact': (EPOCH, (1, True)),
            'emergency': (EPOCH, (2, True)),
            'maps': (EPOCH, (3, True)),
            'webcams': (EPOCH, (4, True)),
            'results': (EPOCH, (5, True)),
            'podcasts': (EPOCH, (6, True)),
        })),
        'rss': (EPOCH, PreferenceSet({
            'hidden_items': (EPOCH, set()),
            'hidden_feeds': (EPOCH, set()),
            'extra_feeds': (EPOCH, set()),
        })),
    }),
}