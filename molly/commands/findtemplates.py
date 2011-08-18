import re, sys, os, os.path

"""
Quick and dirty script to try and figure out unused templates - it's used
something like this:

    find .. -name \*.pyc -exec cat {} \; | molly-admin findtemplates

"""

def command():
    templates = ''
    temps = set()
    for (dirpath, dirnames, filenames) in os.walk('.'):
        path, dir = os.path.split(os.path.normpath(dirpath))
        path, tdir = os.path.split(os.path.normpath(os.path.join(dirpath, '..')))
        path, t2dir = os.path.split(os.path.normpath(os.path.join(dirpath, '..', '..')))
        if tdir == 'templates':
            for filename in filenames:
                file, ext = os.path.splitext(filename)
                temps.add(dir + '/' + file)
                with open(os.path.join(dirpath, filename)) as fd:
                    templates += fd.read()
        elif t2dir == 'templates' and tdir != 'site-media':
            for filename in filenames:
                file, ext = os.path.splitext(filename)
                temps.add(tdir + '/' + dir + '/' + file)
                with open(os.path.join(dirpath, filename)) as fd:
                    templates += fd.read()
    
    used_temps = set()
    for m in re.finditer(r"(render\(\s*.+?\s*,\s*.+?\s*,|get_template\()\s*'(.+?)'\s*\)", sys.stdin.read()):
        used_temps.add(m.group(2))
    
    for m  in re.finditer(r'{% (include|extends) "(.+?).x?html" %}', templates):
        used_temps.add(m.group(2))
    
    
    print "The following templates exist are are used:"
    for t in sorted(temps & used_temps):
        print t
    print
    
    print "The following templates exist, but are not used:"
    for t in sorted(temps - used_temps):
        print t
    print
    
    print "The following templates are used, but do not exist:"
    for t in sorted(used_temps - temps):
        print t
    print
