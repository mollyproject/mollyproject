#!/bin/bash

function build_documentation {
    tag=$1
    rm -rf build
    make html
    API_TEMP=`mktemp -d`
    rm -rf $OUTPUT_DIR/$tag/
    mkdir -p $OUTPUT_DIR/$tag/
    cp -rf build/html/* $OUTPUT_DIR/$tag/
    
    epydoc -o $API_TEMP --html --graph=all -n Molly -u http://mollyproject.org/ --no-private ../molly/
    rm -rf $OUTPUT_DIR/api/$tag/
    mkdir -p $OUTPUT_DIR/api/$tag/
    cp -rf $API_TEMP/* $OUTPUT_DIR/api/$tag/
    rm -rf $API_TEMP
}

OUTPUT_DIR=$1

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