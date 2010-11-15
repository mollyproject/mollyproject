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
    
    # Run tests
    cd $1/demos/molly_oxford/
    python manage.py test $2
else
    echo "$0 path-to-deployment [app-to-test]"
fi
