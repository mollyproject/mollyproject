import platform

if not hasattr(platform, 'linux_distribution'):
    if not hasattr(platform, 'dist'):
        distribution, distribution_version, distribution_id = (None, None, None)
    else:
        distribution, distribution_version, distribution_id = platform.dist()
else:
    distribution, distribution_version, distribution_id = platform.linux_distribution()

from installer.utils import quiet_exec
from installer.sysprep.packagekit import PackagekitSysPreparer, postgres_setup

PYTHON26 = '/usr/bin/python26'

POSTGIS_PATH = '/usr/share/pgsql/postgresql/contrib/lwpostgis.sql'
SPATIAL_REF_SYS_PATH = '/usr/share/pgsql/postgresql/contrib/spatial_ref_sys.sql'
PG_HBA_PATH = '/var/lib/pgsql/data/pg_hba.conf'
POSTGRES_SERVICE = 'postgresql'

class SysPreparer(PackagekitSysPreparer):
    
    PACKAGES = [
                'python26',
                'git',
                'python-setuptools',
                'python26-devel',
                'binutils',
                'libxslt-devel',
                'cyrus-sasl-devel',
                'openldap-devel',
                'ImageMagick',
                'python-virtualenv',
                'python-pip',
                'proj',
                'proj-devel',
                'postgresql',
                'postgresql-server',
                'postgresql-devel',
                'postgresql-contrib',
                'geos-3.1.0',
                'geos-devel-3.1.0',
                'postgis',
                'gdal',
                'libjpeg-devel',
                'make',
                'gcc',
                'openssl-devel',
            ]
    
    def sysprep(self):
        
        # Install EPEL
        quiet_exec(['rpm', '-Uvh', 'http://download.fedora.redhat.com/pub/epel/5/i386/epel-release-5-4.noarch.rpm'], 'EPEL install')
        
        # Install RPM Forge
        rpmforge = tempfile.NamedTemporaryFile()
        rpm = urllib2.urlopen('http://packages.sw.be/rpmforge-release/rpmforge-release-0.5.2-2.el5.rf.i386.rpm', 'RPM Forge install')
        print >>rpmforge, rpm.read()
        rpm.close()
        rpmforge.flush()
        quiet_exec(['rpm', '-Uvh', rpmforge.name])
        rpmforge.close()
        
        # Now actually install packages
        super(SysPreparer, self).sysprep()
