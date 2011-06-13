import os

from distutils.core import Command
from distutils.errors import DistutilsArgError, DistutilsExecError

from installer.deploy import deploy
from installer.virtualenv import Virtualenv, NotAVirtualenvError
from installer.sysprep import SysPreparer
from installer import PIP_PACKAGES

try:
    from installer.sysprep import PYTHON26
except ImportError:
    import sys
    PYTHON26 = sys.executable

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


class CreateVirtualenvCommand(Command):
    
    description = "creates a virtualenv for Molly"
    
    user_options = [
        ('virtualenv=', 'i', 'The path to the virtualenv to create [default=None]'),
        ('force', 'f', 'Force installing, even if virtualenv already exists [default=False]'),
    ]
    
    def initialize_options(self):
        self.virtualenv = None
        self.force = False
    
    def finalize_options(self):
        if self.virtualenv is None:
            raise DistutilsArgError("You must specify a path to create the virtualenv in")
    
    def run(self):
        # Create the virtualenv
        print "Creating a virtualenv for Molly...",
        try:
            venv = Virtualenv.create(self.virtualenv, self.force, PYTHON26)
        except NotAVirtualenvError:
            raise DistutilsArgError('Virtualenv already exists here, use -f to force install')
        print "DONE!"
        
        # Now install our Molly prereqs
        
        print "Installing Python dependencies:"
        pip = os.path.join(self.virtualenv, 'bin', 'pip')
        for name, package in PIP_PACKAGES:
            print " * " + name + '...',
            sys.stdout.flush()
            venv('pip install -U %s' % package)
            print "DONE!"
        print
        return venv

