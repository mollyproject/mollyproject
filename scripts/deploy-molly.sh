#!/bin/bash

while getopts dcf o
do	case "$o" in
	d)	start_dev_server=yes;;
	c)	no_cron=yes;;
        f)      first_migrate=yes;;
	[?])	print >&2 "Usage: $0 [-d] [-c] [-f] path-to-deployment"
		exit 1;;
	esac
done
shift $((OPTIND-1))

if [ -n "$1" ] ; then

    # Make sure we're working from the directory the script is in
    DIR="$( cd "$( dirname "$0" )" && pwd )"
    
    # Set up the virtual environment
    virtualenv --distribute --no-site-packages $1
    
    # Go inside the Python virtual environment
    source $1/bin/activate
    
    # Install our PyZ3950, because the PyPI one is broken
    pip install git+http://github.com/oucs/PyZ3950.git
    
    # Install a fork of Django-compress to correctly handle SSL compressed media
    pip install git+git://github.com/mikelim/django-compress.git#egg=django-compress
    
    # For some reason PIL doesn't work when installed as a dependency
    pip install -U PIL
    
    if [ -n "$start_dev_server" ] ; then
        # Install Molly in development mode
        python $DIR/../setup.py develop
    else
        python $DIR/../setup.py install
    fi
    
    # Install demos
    rm -rf $1/demos
    cp -rf $DIR/../demos/ $1/demos/
    
    # Copy any files in local to the molly_oxford demo - useful for overriding
    # settings.py and secrets.py
    cp -f $DIR/../local/* $1/demos/molly_oxford/
    cd $1/demos/molly_oxford/
    
    # Update batch jobs
    if [ -z "$no_cron" ] ; then
        PYTHONPATH=.. python manage.py create_crontab | python $DIR/merge-cron.py | crontab
    fi
    
    # Build Media
    python manage.py build_static --noinput
    python manage.py synccompress
    python manage.py generate_markers
    python manage.py update_wurfl
    
    # Start server
    if [ -n "$first_migrate" ] ; then
        python manage.py syncdb --all
        python manage.py migrate --fake
    else
        python manage.py syncdb
        python manage.py migrate
    fi
    if [ -n "$start_dev_server" ] ; then
        python manage.py runserver
    fi
    
else
    echo "$0 [-d] [-c] [-f] path-to-deployment"
    echo "    -d: starts the development server afterwards"
    echo "    -c: doesn't alter the crontab"
    echo "    -f: does the first database migration (use on first install)"
fi