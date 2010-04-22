#!/usr/bin/python

import os, sys, os.path, subprocess, shutil

def main(source_path, deploy_path):
    if os.path.exists(deploy_path):
        print "Cannot deploy to path - already exists"
        return 1

    requirements = [l[:-1] for l in open(os.path.join(source_path, "requirements", "core.txt")) if l[:-1]]
    print requirements

    subprocess.call(["virtualenv", "--no-site-packages", deploy_path])
    subprocess.call(["pip", "install", "-U", "-E", deploy_path] + requirements)
    subprocess.call([os.path.join(deploy_path, "bin", "python"), os.path.join(source_path, "setup.py"), "install"])

    # This is a hack to create a file that should have been created at the pip stage.
    cairo_init_path = os.path.join(
        deploy_path, "lib", "python%d.%d" % sys.version_info[:2],
        "site-packages", "cairo", "__init__.py"
    )
    if not os.path.exists(cairo_init_path):
        f = open(cairo_init_path, 'w')
        f.write("from _cairo import *\n")
        f.close()

    # Copy the demos across
    shutil.copytree(
        os.path.join(source_path, 'demos'),
        os.path.join(deploy_path, 'demos'),
    )


if __name__ == '__main__':
    source_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    deploy_path = os.path.abspath(sys.argv[1])
    exit(main(source_path, deploy_path) or 0)
