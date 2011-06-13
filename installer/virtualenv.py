"""
Some convenience functions for dealing with virtualenvs
"""

import os
import sys
from subprocess import Popen, PIPE
import logging
import shutil

from installer.utils import quiet_exec, CommandFailed
from installer import PIP_PACKAGES

try:
    from installer.sysprep import PYTHON26
except ImportError:
    PYTHON26 = sys.executable
    
logger = logging.getLogger(__name__)

class Virtualenv(object):
    """
    A wrapper for running in the virtualenv
    """
    
    def __init__(self, path):
        if not os.path.exists(os.path.join(path, 'bin', 'activate')):
            raise NotAVirtualenvError()
        else:
            self.path = path

    def __call__(self, command, wait=True, quiet=True):
        logger.info('Virtualenv %s: Executing %s', self.path, command)
        command = 'source %s/bin/activate; %s' % (self.path, command)
        self._exec(command, self.path, wait, quiet)
    
    @staticmethod
    def _exec(command, logprefix, wait=True, quiet=True):
        if wait:
            sh_command = ['bash','-c',command]
            if quiet:
                quiet_exec(sh_command, logprefix)
            else:
                process = Popen(sh_command)
                process.wait()
                if process.returncode != 0:
                    raise CommandFailed(process.returncode, None, None)
        else:
            if quiet:
                sh_command = ['bash', '-c', '%s >/dev/null' % command]
            else:
                sh_command = ['bash', '-c', command]
            Popen(sh_command)
    
    @staticmethod
    def create(path, force=False, python=sys.executable):
        """
        Create a virtualenv at the path pointed at by path. If force is True, then anything
        that's already there will be deleted
        """
        
        if os.path.exists(path) and force:
            shutil.rmtree(path)
        elif os.path.exists(path):
            raise NotAVirtualenvError()
        
        if 'VIRTUALENVWRAPPER_HOOK_DIR' in os.environ:
            # Use virtualenvwrapper
            logger.debug('Using virtualenvwrapper to create')
            command = 'mkvirtualenv --python="%s" --distribute --no-site-packages %s' % (python, path)
        else:
            # Use plain old virtualenv
            logger.debug('Using virtualenv to create')
            command = 'virtualenv --python="%s" --distribute --no-site-packages %s' % (python, path)
        Virtualenv._exec(command, 'Create')


class NotAVirtualenvError(Exception):
    pass


def virtualenv_for_molly(path, force=False):
    
    # Create the virtualenv
    print "Creating a virtualenv for Molly...",
    venv = Virtualenv.create(path, force, PYTHON26)
    print "DONE!"
    
    # Now install our Molly prereqs
    
    print "Installing Python dependencies:"
    pip = os.path.join(path, 'bin', 'pip')
    for name, package in PIP_PACKAGES:
        print " * " + name + '...',
        sys.stdout.flush()
        venv('pip install -U %s' % package)
        print "DONE!"
    print
    return venv