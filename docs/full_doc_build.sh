#!/bin/bash

function build_documentation {
    tag=$1
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

build_documentation dev
for tag in `git tag`; do
    git checkout $tag
    build_documentation $tag
done

rm -rf $BUILD_DIR