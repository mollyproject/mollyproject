import os
import string
from random import choice
from shutil import copytree

from distutils.core import Command
from distutils.errors import DistutilsArgError, DistutilsExecError

from installer.deploy import deploy
from installer.virtualenv import Virtualenv, NotAVirtualenvError
from installer.dbcreate import create
from installer import PIP_PACKAGES

try:
    from installer.sysprep import PYTHON26
except (NotImplementedError, ImportError):
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
        self.port = None
    
    def finalize_options(self):
        if self.site_path is None:
            raise DistutilsArgError("You must specify a path to the site to be deployed")
        self.site_path = os.path.abspath(self.site_path)
        if self.virtualenv is None:
            raise DistutilsArgError("You must specify a virtualenv for the site to be deployed into")
        self.virtualenv = os.path.abspath(self.virtualenv)
        if self.listen_externally and not self.development:
            raise DistutilsArgError("You can not listen externally when in non-development mode, only development installs start the server!")
        if self.port and not self.development:
            raise DistutilsArgError("You specify a port when in non-development mode, only development installs start the server!")
        if self.port is None:
            self.port = 8000
    
    def run(self):
        deploy(Virtualenv(self.virtualenv), self.site_path, self.development,
               self.listen_externally, self.port)

try:    
    from installer.sysprep import SysPreparer
except NotImplementedError:
    
    class SysprepCommand(Command):
        
        description = "installs system level dependencies for Molly"
        
        user_options = []
        
        def initialize_options(self):
            pass
        
        def finalize_options(self):
            raise DistutilsExecError('This command is not supported on this system')
        
        def run(self):
            pass
    
else:
    
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

class AbstractDBPrepCommand(Command):
    
    description = "does a one-time configure of a Postgres server"
    
    user_options = [
        ('db-username=', 'u', 'The username of the database superuser to connect as [default=None]'),
        ('db-password=', 'p', 'The password of the database superuser to connect as [default=None]'),
        ('create-template', 't', 'Create the Postgis template database [default=False]'),
        ('configure-security', 's', 'Configure your pg_hba.conf [default=False]'),
    ]
    
    def initialize_options(self):
        self.db_username = None
        self.db_password = None
        self.create_template = False
        self.configure_security = False
    
    def finalize_options(self):
        if not (self.create_template or self.configure_security):
            raise DistutilsArgError('You must specify either -t or -s, or both - nothing to do!')
    
    def run(self):
        pass


class NullDBPrepCommand(AbstractDBPrepCommand):
    
    def finalize_options(self):
        raise DistutilsArgError('DBPrep not supported on this platform')


class DBPrepCommandImpl(AbstractDBPrepCommand):
    
    def run(self):
        postgres_setup()
        if self.create_template:
            create_postgis_template()
        if self.configure_security:
            configure_pg_hba()
    
try:
    from installer.sysprep import postgres_setup
except (ImportError, NotImplementedError):
    def postgres_setup(*args, **kwargs):
        pass

try:
    from installer.dbprep import configure_pg_hba, create_postgis_template
except NotImplementedError:
    
    DBPrepCommand = NullDBPrepCommand
    
else:
    
    DBPrepCommand = DBPrepCommandImpl

class DBCreateCommand(Command):
    
    description = "creates a new user and database for Molly to use"
    
    user_options = [
        ('admin-username=', 'u', 'The username of the database superuser to connect as [default=None]'),
        ('admin-password=', 'p', 'The password of the database superuser to connect as [default=None]'),
        ('molly-username', 'c', 'The username of the database user to create [default=molly]'),
        ('molly-password', 'w', 'The password of the database user to create [default=random]'),
        ('molly-database', 'd', 'Force installing, even if virtualenv already exists [default=molly]'),
    ]
    
    def initialize_options(self):
        self.admin_username = None
        self.admin_password = None
        self.molly_username = 'molly'
        self.molly_password = None
        self.molly_database = 'molly'
    
    def finalize_options(self):
        if self.molly_password is None:
            self.molly_password = ''.join([choice(string.letters + string.digits) for i in range(18)])
    
    def run(self):
        create(self.admin_username, self.admin_password, self.molly_username,
               self.molly_password, self.molly_database)
        print "Username: %s" % self.molly_username
        print "Password: %s" % self.molly_password
        print "Database: %s" % self.molly_database
        print
        print "Please make a note of these, as you will need to place them in your settings.py"


class SiteCreateCommand(Command):
    
    description = "creates a new template site for Molly"
    
    user_options = [
        ('site=', 's', 'The folder to save the site template into [default=None]'),
    ]
    
    def initialize_options(self):
        self.site = None
    
    def finalize_options(self):
        if self.site is None:
            raise DistutilsArgError('You must specify a path to where the site is to be created')
    
    def run(self):
        copytree(os.path.join(os.path.dirname(__file__), 'site'), self.site)
        os.makedirs(os.path.join(self.site, 'site_media'))
        os.makedirs(os.path.join(self.site, 'compiled_media'))
        print "Template created at", os.path.abspath(self.site)

