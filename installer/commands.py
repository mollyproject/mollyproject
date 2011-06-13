import os

from distutils.core import Command
from distutils.errors import DistutilsArgError, DistutilsExecError

from installer.deploy import deploy
from installer.virtualenv import Virtualenv
from installer.sysprep import SysPreparer

class DeployCommand(Command):
    
    description = "performs a deployment of Molly"
    
    user_options = [
        ('site-path=', 's', 'The path of the site to deploy [default=None]'),
        ('virtualenv=', 'i', 'The path to the virtualenv to deploy into [default=None]'),
        ('development', 'd', 'Whether or not this install should be a development install [default=False]'),
        ('listen-externally', 'x', 'Whether or not the development server that is started should listen externally [default=False]'),
        ('port=', 'p', 'The port to start the dev server on [default=8000]')
    ]
    
    def initialize_options(self):
        self.site_path = None
        self.virtualenv = None
        self.development = False
        self.listen_externally = False
        self.dev_server_port = 8000
    
    def finalize_options(self):
        if self.site_path is None:
            raise DistutilsArgError("You must specify a path to the site to be deployed")
        if self.virtualenv is None:
            raise DistutilsArgError("You must specify a virtualenv for the site to be deployed into")
        if self.listen_externally and not self.development:
            raise DistutilsArgError("You can not listen externally when in non-development mode, only development installs start the server!")
        if self.dev_server_port and not self.development:
            raise DistutilsArgError("You specify a port when in non-development mode, only development installs start the server!")
    
    def run(self):
        deploy(Virtualenv(self.virtualenv), self.site_path, self.development,
               self.listen_externally, self.dev_server_port)


class SysprepCommand(Command):
    
    description = "installs system level dependencies for Molly"
    
    user_options = []
    
    def initialize_options(self):
        pass
    
    def finalize_options(self):
        if os.getuid() != 0:
            raise DistutilsExecError('This command can only be run as root')
    
    def run(self):
        sysprepper = SysPreparer()
        sysprepper.sysprep()