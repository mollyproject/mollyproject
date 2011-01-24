"""
Handles generating the settings variables for django-compress
"""

import os, os.path

# os.path.relpath doesn't exist in Py2.5, so we define our own.
# Many thanks to Elliot of saltycrane.com[0] and James Gardner[1].
# [0] http://www.saltycrane.com/blog/2010/03/ospathrelpath-source-code-python-25/
# [1] http://jimmyg.org/work/code/barenecessities/0.2.5/manual.html#the-relpath-function
if not hasattr(os.path, 'relpath'):
    # This code taken from [0], above; modified slightly.
    import posixpath
    def relpath(path, start=posixpath.curdir):
        """Return a relative version of a path"""
        if not path:
            raise ValueError("no path specified")
        start_list = posixpath.abspath(start).split(posixpath.sep)
        path_list = posixpath.abspath(path).split(posixpath.sep)
        # Work out how much of the filepath is shared by start and path.
        i = len(posixpath.commonprefix([start_list, path_list]))
        rel_list = [posixpath.pardir] * (len(start_list)-i) + path_list[i:]
        if not rel_list:
            return posixpath.curdir
        return posixpath.join(*rel_list)
    os.path.relpath = relpath

def get_compress_groups(STATIC_ROOT):
    COMPRESS_CSS, COMPRESS_JS = {}, {}
    
    if not os.path.exists(STATIC_ROOT):
        os.makedirs(STATIC_ROOT)
    
    for directory in os.listdir(STATIC_ROOT):
        # We don't want to compress admin media or already-compressed media.
        if directory in ('admin', 'c', ):
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
                
                path = filename.split('/')[1:-1]
                output_filename = filename.split('/')[-1].rsplit('.', 1)
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
