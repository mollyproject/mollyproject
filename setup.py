import ez_setup
ez_setup.use_setuptools()

from setuptools import setup
from distutils.command.install import INSTALL_SCHEMES
from molly import __version__ as molly_version
import os

#################################
# BEGIN borrowed from Django    #
# licensed under the BSD        #
# http://www.djangoproject.com/ #
#################################

def fullsplit(path, result=None):
    """
    Split a pathname into components (the opposite of os.path.join) in a
    platform-neutral way.
    """
    if result is None:
        result = []
    head, tail = os.path.split(path)
    if head == '':
        return [tail] + result
    if head == path:
        return result
    return fullsplit(head, [tail] + result)

# Tell distutils to put the data_files in platform-specific installation
# locations. See here for an explanation:
# http://groups.google.com/group/comp.lang.python/browse_thread/thread/35ec7b2fed36eaec/2105ee4d9e8042cb
for scheme in INSTALL_SCHEMES.values():
    scheme['data'] = scheme['purelib']

# Compile the list of packages available, because distutils doesn't have
# an easy way to do this.
packages, data_files = [], []
root_dir = os.path.dirname(__file__)
if root_dir != '':
    os.chdir(root_dir)
molly_dir = 'molly'

for dirpath, dirnames, filenames in os.walk(molly_dir):
    # Ignore dirnames that start with '.'
    for i, dirname in enumerate(dirnames):
        if dirname.startswith('.'): del dirnames[i]
    if '__init__.py' in filenames:
        packages.append('.'.join(fullsplit(dirpath)))
    elif filenames:
        data_files.append([dirpath, [os.path.join(dirpath, f) for f in filenames]])

#################################
# END borrowed from Django      #
#################################

setup(
    name = 'molly',
    version = molly_version,
    url = 'http://mollyproject.org/',
    author = 'University of Oxford',
    description ="A framework for building mobile information portals",
    packages = packages,
    data_files = data_files, 
    classifiers=[
        'Framework :: Django',
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: Academic Free License',
        'Intended Audience :: Education',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Education',
        'Topic :: Internet',
    ],
    install_requires = [
        "python-Levenshtein",
        "pywurfl",
        "ply",
        "PyZ3950", # The one in PyPI is broken! You should install the one from
                   # https://github.com/alexdutton/PyZ3950/ *BEFORE* running
                   # this script
        "feedparser>=5.0",
        "simplejson",
        "rdflib",
        "python-dateutil==1.5",
        "Django==1.3",
        "oauth==1.0.1",
        "psycopg2",
        "PIL",
        "lxml",
        "python-ldap",
        "django-compress",
        "python-memcached",
        "South",
        "suds",
        "django-slimmer",
        'pyyaml',
    ],
    dependency_links = [
        'http://pylevenshtein.googlecode.com/files/python-Levenshtein-0.10.1.tar.bz2#egg=python-Levenshtein'
    ]
)



