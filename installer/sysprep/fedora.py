import sys
import os

from installer.sysprep.packagekit import PackagekitSysPreparer, postgres_setup

POSTGIS_PATH = '/usr/share/pgsql/contrib/postgis-1.5/postgis.sql'
SPATIAL_REF_SYS_PATH = '/usr/share/pgsql/contrib/postgis-1.5/spatial_ref_sys.sql'
PG_HBA_PATH = '/var/lib/pgsql/data/pg_hba.conf'
POSTGRES_SERVICE = 'postgresql'

class SysPreparer(PackagekitSysPreparer):
    
    PACKAGES = [
                'python-virtualenv',
                'python-pip',
                'libxml-devel',
                'libxslt-devel',
                'python-devel',
                'postgresql-devel',
                'openldap-devel',
                'openssl-devel',
                'postgis',
                'gdal-python',
                'proj',
                'postgresql-server',
                'geos',
                'httpd',
                'libjpeg-devel',
                'imagemagick',
                'gcc',
                'make',
                'git',
                'libyaml',
            ]