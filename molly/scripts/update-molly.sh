#!/bin/bash

if [ -n "$1" ] ; then

    # Make sure we're working from the directory the script is in
    DIR="$( cd "$( dirname "$0" )" && pwd )"
    
    # Go inside the virtual environment
    source $1/bin/activate
    
    # Update molly
    python $DIR/../setup.py install
    
    # Rebuild demos
    rm -rf $1/demos
    cp -rf $DIR/../demos/ $1/demos/
    
    # Copy any files in local to the molly_oxford demo - useful for overriding
    # settings.py and secrets.py
    cp -f $DIR/../local/* $1/demos/molly_oxford/
    
    # Set up media directories
    cd $1/demos/molly_oxford/
    mkdir media
    mkdir -p media/c/css
    mkdir media/c/css/groups
    mkdir media/c/css/core
    mkdir media/c/blueprint
    mkdir -p media/c/openlayers/theme/default
    mkdir media/c/js
    mkdir media/c/js/groups
    mkdir media/c/js/devices
    
    # Build media
    python manage.py build_static --noinput
    python manage.py synccompress
    
    # Update batch jobs
    PYTHONPATH=.. python manage.py create_crontab | python $DIR/merge-cron.py | crontab
    
    # Run server
    python manage.py syncdb
    python manage.py runserver
else
    echo "$0 path-to-deployment"
fi
