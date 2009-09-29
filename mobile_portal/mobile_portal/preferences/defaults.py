from datetime import datetime
from preferences import PreferenceSet, EmptyPreferenceSet

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
            'maps': (EPOCH, (2, True)),
            'webcams': (EPOCH, (3, True)),
            'results': (EPOCH, (4, True)),
            'podcasts': (EPOCH, (5, True)),
            'rss': (EPOCH, (6, True)),
            'z3950': (EPOCH, (7, True)),
        })),
        'rss': (EPOCH, PreferenceSet({
            'hidden_items': (EPOCH, set()),
            'hidden_feeds': (EPOCH, set()),
            'extra_feeds': (EPOCH, set()),
        })),
        'podcasts': (EPOCH, PreferenceSet({
            'use_itunesu': (EPOCH, PreferenceSet({
            })),
        })),
        'maps': (EPOCH, PreferenceSet({
            'favourites': (EPOCH, []),
        })),
    }),
}

def get_defaults(k):
    if not k:
        return EmptyPreferenceSet()
    ks = k.split('/')
    ps = defaults[ks[0]]
    for k in ks[1:]:
        ps = ps[k]
    return ps
