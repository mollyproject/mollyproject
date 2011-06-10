from installer.sysprep.packagekit import PackagekitSysPreparer

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
            ]