#!/bin/bash

if [ -n "$1" ] ; then

    # Make sure we're working from the directory the script is in
    DIR="$( cd "$( dirname "$0" )" && pwd )"
    
    # Set up the virtual environment
    virtualenv --distribute --no-site-packages $1
    
    # Go inside the Python virtual environment
    source $1/bin/activate
    
    # Install our PyZ3950, because the PyPI one is broken
    pip install git+http://github.com/oucs/PyZ3950.git
    
    # Install Molly in development mode
    python $DIR/../setup.py develop
    
    # Install demos
    rm -rf $1/demos
    cp -rf $DIR/../demos/ $1/demos/
    
    # Copy any files in local to the molly_oxford demo - useful for overriding
    # settings.py and secrets.py
    cp -f $DIR/../local/* $1/demos/molly_oxford/
    cd $1/demos/molly_oxford/
    
    # Update batch jobs
    PYTHONPATH=.. python manage.py create_crontab | python $DIR/merge-cron.py | crontab
    
    # Build Media
    python manage.py build_static --noinput
    python manage.py synccompress
    python manage.py generate_markers
    
    # Start server
    python manage.py syncdb
    python manage.py runserver
else
    echo "$0 path-to-deployment"
fi