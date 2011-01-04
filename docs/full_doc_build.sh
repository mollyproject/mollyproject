#!/bin/bash

function build_documentation {
    tag=$1
    cd docs
    rm -rf build
    make html
    rm -rf $OUTPUT_DIR/$tag/
    mkdir $OUTPUT_DIR/$tag/
    cp -rf build/html/* $OUTPUT_DIR/$tag/
}

REPO=git://github.com/mollyproject/mollyproject.git
OUTPUT_DIR=$1

if [ -z "$OUTPUT_DIR" ] ; then
    echo "$0 <path-to-doc-root>"
    exit;
fi

BUILD_DIR=`mktemp -d`
git clone $REPO $BUILD_DIR

cd $BUILD_DIR

build_documentation dev
for tag in `git tag`; do
    build_documentation $tag
done

rm -rf $BUILD_DIR