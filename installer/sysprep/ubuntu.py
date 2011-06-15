from installer.utils import quiet_exec

class AptSysPreparer(object):
    
    @property
    def PACKAGES(self):
        raise NotImplementedError()
    
    def _install(self):
        
        quiet_exec(['apt-get', '-y', 'update'], 'Apt')
        quiet_exec(['apt-get', '-y', 'install'] + self.PACKAGES, 'Apt')
    
    def sysprep(self):
        self._install()
        quiet_exec(['easy_install', '-U', 'virtualenv'], 'Apt')