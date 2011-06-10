from distutils.core import Command
from distutils.errors import DistutilsArgError

from installer.deploy import deploy
from installer.virtualenv import Virtualenv

class DeployCommand(Command):
    
    description = "performs a deployment of Molly"
    
    user_options = [
        ('site-path=', 's', 'The path of the site to deploy [default=None]'),
        ('virtualenv=', 'i', 'The path to the virtualenv to deploy into [default=None]'),
        ('development', 'd', 'Whether or not this install should be a development install [default=False]')
    ]
    
    def initialize_options(self):
        self.site_path = None
        self.virtualenv = None
        self.development = False
    
    def finalize_options(self):
        if self.site_path is None:
            raise DistutilsArgError("You must specify a path to the site to be deployed")
        if self.virtualenv is None:
            raise DistutilsArgError("You must specify a virtualenv for the site to be deployed into")
    
    def run(self):
        deploy(Virtualenv(self.virtualenv), self.site_path, self.development)