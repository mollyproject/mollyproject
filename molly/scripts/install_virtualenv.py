#!/usr/bin/env python

import os, sys, os.path, subprocess, shutil

def cairo_hack(source_path, deploy_path):
    # This is a hack to create a file that should have been created at the pip stage.
    cairo_init_path = os.path.join(
        deploy_path, "lib", "python%d.%d" % sys.version_info[:2],
        "site-packages", "cairo", "__init__.py"
    )
    if not os.path.exists(cairo_init_path):
        f = open(cairo_init_path, 'w')
        f.write("from _cairo import *\n")
        f.close()

def cairo_link(source_path, deploy_path):
    for path in sys.path:
        path = os.path.join(path, 'cairo')
        if os.path.exists(path):
            break
    else:
        raise ImportError

    os.link(path, os.path.join(deploy_path,
                               "lib",
                               "python%d.%d" % sys.version_info[:2],
                               "site-packages",
                               "cairo"))

def copy_demos(source_path, deploy_path):
    # Copy the demos across
    shutil.copytree(
        os.path.join(source_path, 'demos'),
        os.path.join(deploy_path, 'demos'),
    )

def system_cairo_required():
    try:
        version = open('/etc/debian_version', 'r').read()
        major = int(version.split('.')[0])
        return major <= 5
    except (IOError, ValueError):
        return False


def main(source_path, deploy_path):
    if os.path.exists(deploy_path):
        print "Cannot deploy to path - already exists"
        return 1

    use_system_cairo = system_cairo_required()

    commands = [
        ('Creating', 'virtual environment', ["virtualenv", "--no-site-packages", deploy_path]),
    ]

    requirements = [l[:-1] for l in open(os.path.join(source_path, "requirements", "core.txt")) if l[:-1]]

    if use_system_cairo:
        requirements.remove('pycairo')

    for requirement in requirements:
        commands.append(
            ('Installing', requirement,
             ["pip", "install", "-U", "-E", deploy_path, requirement])
        )

    if use_system_cairo:
        commands += [
            ('Linking', 'cairo', cairo_link),
        ]
    else:
        commands += [
            ('Tidying', 'cairo', cairo_hack),
        ]


    commands += [
        ('Deploying', 'molly',
         [os.path.join(deploy_path, "bin", "python"), os.path.join(source_path, "setup.py"), "install"]),
        ('Copying', 'demos', copy_demos),
    ]


    stdout_log = open('molly.stdout.log', 'w')
    stderr_log = open('molly.stderr.log', 'w')
    succeeded = True
    for i, (action, item, command) in enumerate(commands):
        print "%s %s (%2d/%2d)" % (action[:12].ljust(12), item[:40].ljust(40), (i+1), len(commands)),
        if callable(command):
            try:
                return_code = command(source_path, deploy_path) or 0
            except Exception:
                return_code = 1
        else:
            return_code = subprocess.call(command, stdout=stdout_log, stderr=stderr_log)
        print "[%s]" % ('FAILED' if return_code else '  OK  ')
        succeeded = succeeded and (return_code == 0)

    if succeeded:
        print """
Molly was successfully installed to %(deploy_path)s.
The following command will take you inside your virtualenv:

$ source %(activate)s""" % {
            'deploy_path': deploy_path,
            'activate': os.path.join(deploy_path, "bin", "activate"),
        }
    else:
        print """
The installation failed. You may find useful information in molly.stdout.log
and molly.stderr.log. For assistance, please e-mail the mailing list at
mollyproject-devel@lists.sourceforge.net or join the #molly IRC channel on
irc.freenode.net.""" 


if __name__ == '__main__':
    source_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    deploy_path = os.path.abspath(sys.argv[1])
    exit(main(source_path, deploy_path) or 0)
