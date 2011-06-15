#################################
# BEGIN borrowed from Django    #
# licensed under the BSD        #
# http://www.djangoproject.com/ #
#################################

import os
from subprocess import Popen, PIPE
import logging

logger = logging.getLogger(__name__)

def fullsplit(path, result=None):
    """
    Split a pathname into components (the opposite of os.path.join) in a
    platform-neutral way.
    """
    if result is None:
        result = []
    head, tail = os.path.split(path)
    if head == '':
        return [tail] + result
    if head == path:
        return result
    return fullsplit(head, [tail] + result)

def get_packages_and_data(root_dir):
    # Compile the list of packages available, because distutils doesn't have
    # an easy way to do this.
    packages, data_files = [], []
    if root_dir != '':
        os.chdir(root_dir)
    molly_dir = 'molly'
    
    for dirpath, dirnames, filenames in os.walk(molly_dir):
        # Ignore dirnames that start with '.'
        for i, dirname in enumerate(dirnames):
            if dirname.startswith('.'): del dirnames[i]
        if '__init__.py' in filenames:
            packages.append('.'.join(fullsplit(dirpath)))
        elif filenames:
            data_files.append([dirpath, [os.path.join(dirpath, f) for f in filenames]])
    
    return packages, data_files

#################################
# END borrowed from Django      #
#################################

def quiet_exec(command, logprefix):
    process = Popen(command, stdout=PIPE, stderr=PIPE)
    stdoutdata, stderrdata = process.communicate()
    logger.debug('%s: %s: STDOUT: %s', logprefix, (' ').join(command), stdoutdata)
    logger.debug('%s: %s: STDERR: %s', logprefix, (' ').join(command), stderrdata)
    if process.returncode != 0:
        raise CommandFailed((' ').join(command), process.returncode, stdoutdata, stderrdata)


class CommandFailed(Exception):
    
    def __init__(self, command, retcode, stdout, stderr):
        self.command = command
        self.stdout = stdout
        self.stderr = stderr
        self.retcode = retcode
    
    def __str__(self):
        return """CommandFailed: %s
STDOUT

%s

STDERR

%s
""" % (self.command, self.stdout, self.stderr)