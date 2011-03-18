#!/bin/bash

function build_documentation {
    tag=$1
    rm -rf build
    make html SPHINXBUILD="$PYTHON `which sphinx-build`"
    API_TEMP=`mktemp -d`
    rm -rf $OUTPUT_DIR/$tag/
    mkdir -p $OUTPUT_DIR/$tag/
    cp -rf build/html/* $OUTPUT_DIR/$tag/
    
    $PYTHON `which epydoc` -o $API_TEMP --html --graph=all -n Molly -u http://mollyproject.org/ --no-private ../molly/
    rm -rf $OUTPUT_DIR/api/$tag/
    mkdir -p $OUTPUT_DIR/api/$tag/
    cp -rf $API_TEMP/* $OUTPUT_DIR/api/$tag/
    rm -rf $API_TEMP
}

OUTPUT_DIR=$1
PYTHON=$2
if [ -z "$PYTHON" ] ; then
    PYTHON='python'
    SPHINXBUILD="`which spinx-build`"
else
    SPHINXBUILD="`dirname $PYTHON`/sphinx-build"
fi

if [ -z "$OUTPUT_DIR" ] ; then
    echo "$0 <path-to-doc-root>"
    exit;
fi

build_documentation dev
for tag in `git tag`; do
    git checkout $tag
    build_documentation $tag
done

rm -rf $BUILD_DIR