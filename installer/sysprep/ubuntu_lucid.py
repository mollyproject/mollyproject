from installer.sysprep.ubuntu import AptSysPreparer

class SysPreparer(AptSysPreparer):
    
    PACKAGES = [
            'python-pip',
            'build-essential',
            'postgis',
            'python-gdal',
            'proj',
            'libgeos-3.1.0',
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
        ]