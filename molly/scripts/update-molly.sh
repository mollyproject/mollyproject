#!/bin/bash

# Put your files (settings.py and secrets.py) in local, they override the
# default ones when updating

if [ -n "$1" ] ; then
    DIR="$( cd "$( dirname "$0" )" && pwd )"
    source $1/bin/activate
    python $DIR/../setup.py install
    rm -rf $1/demos
    cp -rf $DIR/../demos/ $1/demos/
    cp -f $DIR/../local/* $1/demos/molly_oxford/
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
    python manage.py build_static --noinput
    python manage.py synccompress
    python manage.py syncdb
    python manage.py runserver
else
    echo "$0 path-to-deployment"
fi
