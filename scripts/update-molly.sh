#!/bin/bash

if [ -n "$1" ] ; then

    # Make sure we're working from the directory the script is in
    DIR="$( cd "$( dirname "$0" )" && pwd )"
    
    # Go inside the virtual environment
    source $1/bin/activate
    
    # Install Molly in development mode
    python $DIR/../setup.py develop
    mkdir $DIR/../media/
    
    # Rebuild demos
    rm -rf $1/demos
    
    # Copy any files in local to the molly_oxford demo - useful for overriding
    # settings.py and secrets.py
    cp -f $DIR/../local/* $1/demos/molly_oxford/
    
    # Build media
    cd $1/demos/molly_oxford/
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
