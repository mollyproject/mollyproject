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
                if root == settings.STATIC_ROOT:
                    # Don't cache admin media, desktop or markers
                    if 'admin' in dirs: dirs.remove('admin')
                    if 'desktop' in dirs: dirs.remove('desktop')
                    if 'markers' in dirs: dirs.remove('markers')
                
                if root == os.path.join(settings.STATIC_ROOT, 'touchmaplite', 'images'):
                    # Don't cache touchmaplite markers, we don't use them
                    if 'markers' in dirs: dirs.remove('markers')
                    if 'iui' in dirs: dirs.remove('iui')
                url = '/'.join(root.split(os.sep)[static_prefix_length:])
                for file in files:
                    # Don't cache uncompressed JS/CSS
                    _, ext = os.path.splitext(file)
                    if ext in ('.js','.css') and 'c' != url.split('/')[0]:
                        continue
                    
                    # Don't cache ourselves!
                    if file == 'cache.manifest':
                        continue
                    
                    print >>cache_manifest, "%s%s/%s" % (settings.STATIC_URL, url, file)