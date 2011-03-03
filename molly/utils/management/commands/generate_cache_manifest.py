import os
import os.path

from django.core.management.base import NoArgsCommand
from django.conf import settings

class Command(NoArgsCommand):
    
    can_import_settings = True

    def handle_noargs(self, **options):
        cache_manifest_path = os.path.join(settings.STATIC_ROOT,
                                           'cache.manifest')
        static_prefix_length = len(settings.STATIC_ROOT.split(os.sep))
        with open(cache_manifest_path, 'w') as cache_manifest:
            print >>cache_manifest, "CACHE MANIFEST"
            print >>cache_manifest, "CACHE:"
            for root, dirs, files in os.walk(settings.STATIC_ROOT):
                url = '/'.join(root.split(os.sep)[static_prefix_length:])
                for file in files:
                    print >>cache_manifest, "%s%s/%s" % (settings.STATIC_URL, url, file)