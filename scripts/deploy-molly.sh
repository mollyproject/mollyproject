#!/bin/bash

while getopts dc o
do	case "$o" in
	d)	start_dev_server=yes;;
	c)	no_cron=yes;;
	[?])	print >&2 "Usage: $0 [--dev] [--no-cron] path-to-deployment"
		exit 1;;
	esac
done
shift $((OPTIND-1))

if [ -n "$1" ] ; then

    # Make sure we're working from the directory the script is in
    DIR="$( cd "$( dirname "$0" )" && pwd )"
    
    # Set up the virtual environment
    python $DIR/install_virtualenv.py $1
    
    # Go inside the Python virtual environment
    source $1/bin/activate
    
    # Install Molly
    python $DIR/../setup.py install
    
    # An empty directory is needed here otherwise things error later
    mkdir $1/lib/python`python -V 2>&1 | cut -d" " -f2`/site-packages/molly/media
    
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
    
    # Start server
    python manage.py syncdb
    python manage.py migrate
    if [ -n "$start_dev_server" ] ; then
        python manage.py runserver
    fi
    
else
    echo "$0 [--dev] [--no-cron] path-to-deployment"
    echo "    -d: starts the development server afterwards"
    echo "    -c: doesn't alter the crontab"
fi