from installer.sysprep.ubuntu import AptSysPreparer

POSTGIS_PATH = '/usr/share/postgresql/8.4/contrib/postgis-1.5/postgis.sql'
SPATIAL_REF_SYS_PATH = '/usr/share/postgresql/8.4/contrib/postgis-1.5/spatial_ref_sys.sql'
PG_HBA_PATH = '/etc/postgresql/8.4/main/pg_hba.conf'
POSTGRES_SERVICE = 'postgresql'

class SysPreparer(AptSysPreparer):
    
    PACKAGES = [
            'python-pip',
            'build-essential',
            'postgis',
            'python-gdal',
            'proj',
            'libgeos-3.2.0',
            'binutils',
            'libgdal1-1.6.0',
            'postgresql-8.4',
            'postgresql-8.4-postgis',
            'postgresql-server-dev-8.4',
            'python-setuptools',
            'python-dev',
            'libxslt-dev',
            'libldap2-dev',
            'libsasl2-dev',
            'libjpeg-dev',
            'imagemagick',
            'git-core',
            'libyaml',
        ]