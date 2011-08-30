"""
Wrapper for installations on packagekit/yum distributions
"""

import os, sys
from molly.installer.utils import quiet_exec

try:
    # Use the Packagekit library if this exists
    import packagekit.client
    
except ImportError:
    
    class PackagekitSysPreparer(object):
        
        @property
        def PACKAGES(self):
            raise NotImplementedError()
        
        def _install(self):
            
            quiet_exec(['yum', '-y', 'install'] + self.PACKAGES, 'Yum')
        
        def sysprep(self):
            self._install()
    
else:
    
    class PackagekitSysPreparer(object):
        
        @property
        def PACKAGES(self):
            raise NotImplementedError()
        
        def _install(self):
            
            from packagekit.enums import FILTER_INSTALLED
            
            pk = packagekit.client.PackageKitClient()
            
            packages = pk.resolve(self.PACKAGES)
            all_packages = [package.id for package in pk.get_packages(filters=FILTER_INSTALLED)]
            to_install = [package for package in packages if package.id not in all_packages]
            
            if len(to_install) == 0:
                print "All prerequisites satisfied! Continuing..."
            else:
                print "The following packages must be installed to satisfy Molly's prerequisites:"
                for package in to_install:
                    print " * ", package
                raw_input('Press Enter to install these packages, or Ctrl+C to exit')
                
                pk.install_packages(to_install)
        
        def sysprep(self):
            self._install()


def postgres_setup():
    if os.getuid() != 0:
        print "Can't start postgres - not root, skipping..."
    else:
        print "Starting Postgres...",
        sys.stdout.flush()
        quiet_exec(['chkconfig', 'postgresql', 'on'], 'dbprep')
        quiet_exec(['service', 'postgresql', 'initdb'], 'dbprep')
        quiet_exec(['service', 'postgresql', 'start'], 'dbprep')
        print "DONE!"