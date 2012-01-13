"""
Handles generating the settings variables for django-compress
"""

import os, os.path

def get_compress_groups(STATIC_ROOT):
    COMPRESS_CSS, COMPRESS_JS = {}, {}
    
    if not os.path.exists(STATIC_ROOT):
        os.makedirs(STATIC_ROOT)
    
    for directory in os.listdir(STATIC_ROOT):
        # We don't want to compress admin media or already-compressed media.
        # Due to the structure of the leaflet directory (as its distributed like
        # that) and the fact that it's already minified), we don't compress it
        # blueprint is only used for desktop site, no need to compress it
        if directory in ('admin', 'c', 'leaflet', 'blueprint',):
            continue
        directory = os.path.join(STATIC_ROOT, directory)
        for root, dirs, files in os.walk(directory):
            for filename in files:
                filename = os.path.relpath(os.path.join(root, filename), STATIC_ROOT)
                if filename.endswith('.css'):
                    compress = COMPRESS_CSS
                elif filename.endswith('.js'):
                    compress = COMPRESS_JS
                else:
                    continue
                
                path = filename.split(os.sep)[1:-1]
                output_filename = filename.split(os.sep)[-1].rsplit('.', 1)
                group = '-'.join(path + [output_filename[0],])
                if group.startswith('css-') or group.startswith('js-'):
                    group = group.split('-', 1)[1]
                if not group in compress:
                    output_filename = '.'.join((output_filename[0], 'v?', output_filename[1]))
                    output_filename = os.path.join(os.path.join('c', *path), output_filename)

                    # Create the target directory if it doesn't already exist.
                    if not os.path.exists(os.path.join(STATIC_ROOT, os.path.dirname(output_filename))):
                        os.makedirs(os.path.join(STATIC_ROOT, os.path.dirname(output_filename)))

                    compress[group] = {
                        'source_filenames': (),
                        'output_filename': output_filename,
                        'extra_context': {},
                    }
                compress[group]['source_filenames'] += (filename,)
    
    return COMPRESS_CSS, COMPRESS_JS
