"""
Takes a site and installs it
"""

import os
import sys
import logging
import shutil

from installer.utils import CommandFailed

logger = logging.getLogger(__name__)

def deploy(venv, site_path, development=False):
    """
    Take the site in "site_path" and deploy it into the virtualenv. The
    development argument specifies whether or not this should be a development
    install.
    """
    
    logger.info('Doing a %s install into %s using site %s',
                'development' if development else 'production',
                venv.path, site_path)
    
    if not development:
        # Copy folder to deployment dir when not in dev mode
        
        site_name = os.path.split(site_path)[-1]
        site_deploy_path = os.path.join(venv.path, site_name)
        
        if os.path.exists(site):
            logger.debug('Removing %s as it already exists in the install location',
                         site_deploy_path)
            shutil.rmtree(site)
        shutil.copytree(site_path, site_deploy_path)
    
    else:
        
        # Development installs have deployments running from the site folder
        site_deploy_path = site_path
    
    # Determine if our deployed site has its own requirements that need satisfying
    if os.path.exists(os.path.join(site_path, 'requirements.txt')):
        print "Installing site requirements...",
        sys.stdout.flush()
        venv("pip install -r %s/requirements.txt" % site_path)
        print "DONE!"
    
    # Okay, now install Molly
    print "Installing Molly...",
    sys.stdout.flush()
    molly_setup = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'setup.py')
    if development:
        venv('python %s develop' % molly_setup)
    else:
        venv('python %s install' % molly_setup)
    print "DONE!"
    
    # Do syncdb
    venv("python %s/manage.py sync_and_migrate" % site_path, quiet=False)
    
    # Okay, now build media
    print "Building media... (this may take some time)",
    sys.stdout.flush()
    try:
        venv('python -c "from molly.wurfl import wurfl_data"')
    except CommandFailed:
        logger.info("Building Wurfl file")
        venv("python %s/manage.py update_wurfl" % site_path)
    venv("python %s/manage.py generate_markers --lazy" % site_path)
    if development:
        venv("python %s/manage.py collectstatic --noinput -l" % site_path)
    else:
        venv("python %s/manage.py collectstatic --noinput" % site_path)
    venv("python %s/manage.py synccompress" % site_path)
    #venv("python %s/manage.py generate_cache_manifest" % site_path)
    venv("python %s/manage.py create_crontab | crontab" % site_path)
    print "DONE!"
    
    # Start dev server
    if development:
        try:
            venv('python %s/manage.py runserver' % site_path, wait=True, quiet=False)
        except CommandFailed:
            pass
