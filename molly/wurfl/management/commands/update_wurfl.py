import tempfile, os, os.path, gzip, urllib, itertools, optparse, pkg_resources, sys
import pdb, subprocess, shutil
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
from xml.etree import ElementTree as ET

from django.core.management.base import NoArgsCommand
from pywurfl import wurflprocessor

class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list
    help = "Updates wurfl data"

    requires_model_validation = False

    WURFL_URL = 'http://kent.dl.sourceforge.net/project/wurfl/WURFL/latest/wurfl-latest.xml.gz'
    WEB_PATCH_URL = 'http://wurfl.sourceforge.net/web_browsers_patch.xml'

    def handle_noargs(self, **options):
        tempdir = tempfile.mkdtemp()
        
        final_filename = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', 'wurfl_data.py'))
        local_filename = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'local_patch.xml'))
        
        try:
            wurfl_gz = urllib.urlopen(Command.WURFL_URL)
            wurfl_f = gzip.GzipFile(fileobj=StringIO(wurfl_gz.read()))
            wurfl_filename = os.path.join(tempdir, 'wurfl.xml')

            web_patch_f = urllib.urlopen(Command.WEB_PATCH_URL)
            local_patch_f = open(local_filename, 'r')
            
            wurfl = ET.parse(wurfl_f)
            web_patch = ET.parse(web_patch_f)
            local_patch = ET.parse(local_patch_f)
            
            devices = {}
            devices_et = itertools.chain(
                wurfl.findall('devices/device'),
                web_patch.findall('devices/device'),
                local_patch.findall('devices/device'),
            )
            
            root = ET.Element('wurfl')
            root.append(wurfl.find('version'))
            devices_out = ET.SubElement(root, 'devices')
           
            for device_et in devices_et:
                devices_out.append(device_et)
                
            out_filename = os.path.join(tempdir, 'wurfl.xml')
            gen_filename = os.path.join(tempdir, 'wurfl.py')
            ET.ElementTree(root).write(out_filename)

            subprocess.call(['wurfl2python.py', out_filename, '-o', gen_filename])
            
            shutil.move(gen_filename, final_filename)

        finally:
            shutil.rmtree(tempdir)
