import os
from shutil import copytree

def command(path):
    
    copytree(os.path.join(os.path.dirname(__file__), 'site_template'), path)
    os.makedirs(os.path.join(path, 'site_media'))
    os.makedirs(os.path.join(path, 'compiled_media'))
    print "Template created at", os.path.abspath(path)
