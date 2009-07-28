# WURFL Processor - Wireless Universal Resource File Processor in Python
# Copyright (C) 2004-2009 Armand Lynch
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation; either version 2.1 of the License, or (at your
# option) any later version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#
# Armand Lynch <lyncha@users.sourceforge.net>

__doc__ = \
"""
WURFL processing utility.
"""


import sys
from optparse import OptionParser

try:
    from xml.etree.ElementTree import parse
except ImportError:
    try:
        from cElementTree import parse
    except ImportError:
        from elementtree.ElementTree import parse

from pywurfl.exceptions import WURFLException


__author__ = "Armand Lynch <lyncha@users.sourceforge.net>"
__contributors__ = "Pau Aliagas <pau@newtral.org>"
__copyright__ = "Copyright 2004-2009, Armand Lynch"
__license__ = "LGPL"
__url__ = "http://celljam.net/"
__all__ = ['DeferredDeviceError', 'DeviceHandler', 'WurflProcessor', 'main',
           'op']


class DeferredDeviceError(WURFLException):
    """
    Deferred Device Error Exception

    Raised when all devices have been processed and there are still deferred
    devices.
    """
    pass


class DeviceHandler(object):
    """
    Base class for DeviceHandler objects
    """

    def __init__(self, device):
        """
        @param device: An elementtree.Element instance of a device element in
                       a WURFL xml file.
        @type device: elementtree.Element
        """

        self.devua = device.attrib["user_agent"]
        self.devid = device.attrib["id"]
        self.parent = device.attrib["fall_back"]
        if ("actual_device_root" in device.attrib and
            device.attrib['actual_device_root'].lower() == "true"):
            self.actual_device_root = True
        else:
            self.actual_device_root = False
        self.capabilities = {}


class WurflProcessor(object):
    """
    WURFL Processing Class
    """

    def __init__(self, wurflxml, device_handler=None, options=None):
        """
        @param wurflxml: A filename of the WURFL.xml file to process. The
                         filename can be a regular, zip, bzip2 or gzipped file.
        @type wurflxml: string
        @param device_handler: A reference to a subclass of DeviceHandler.
        @type device_handler: DeviceHandler
        @param options: A dictionary of additional user specified options.
        @type options: dict
        """
        self.wurflxml = wurflxml
        if wurflxml.endswith(".gz"):
            import gzip
            file_handle = gzip.open(wurflxml, "rb")
        elif wurflxml.endswith(".bz2"):
            from bz2 import BZ2File
            file_handle = BZ2File(wurflxml)
        elif wurflxml.endswith(".zip"):
            from zipfile import ZipFile
            from cStringIO import StringIO
            zipfile = ZipFile(wurflxml)
            file_handle = StringIO(zipfile.read(zipfile.namelist()[0]))
        else:
            file_handle = file(wurflxml,"rb")
        self.file_handle = file_handle

        self.tree = parse(self.file_handle)
        self.root = self.tree.getroot()

        if options is not None:
            for key in options:
                self.__setattr__(key, options[key])

            self.process_options()

        self.device_handler = device_handler
        self.deferred = {}
        self.deferred_len = 0
        self.done = {}

    def process_options(self):
        """
        Hook called to process any additional options.
        """
        pass

    def start_process(self):
        """
        Hook called in before any processing is done.
        """
        pass

    def end_process(self):
        """
        Hook called when processing is done.
        """
        pass

    def handle_device(self, devobj):
        """
        Hook called to handle a device.

        This hook is called when all of the capabilities of a device have been
        processed and its fall_back has already been processed.
        """
        pass

    def process_deferred(self):
        """
        Hook called to handle deferred device objects.

        This hook is called to process any deferred devices (devices that have
        been defined in the WURFL before their fall_back has been defined). It
        is called after any device has been handled and also called in a loop
        after all device definitions in the WURFL have been exhausted.
        """
        todel = []
        for parent in self.deferred:
            if parent in self.done:
                for devobj in self.deferred[parent]:
                    self.done[devobj.devid] = devobj
                    self.handle_device(devobj)
                todel.append(parent)
        for handled_device in todel:
            del(self.deferred[handled_device])

    def process_device(self, devobj):
        """
        Hook called after a new device object has been instantiated.
        """
        pass

    def process_group(self, devobj, group):
        """
        Hook called when a new WURFL group is encountered.
        """
        pass

    def process_capability(self, devobj, group, capability):
        """
        Hook called when a new WURFL capability is encountered.
        """
        pass

    def process_new_deferred(self, devobj):
        """
        Hook called when a device is initially deferred.
        """
        pass

    def process(self):
        """
        Main WURFL processing method.
        """

        self.deferred = {}
        self.done = {}

        self.start_process()

        for device in self.root.find("devices"):
            if self.device_handler:
                devobj = self.device_handler(device)
            else:
                devobj = None
            self.process_device(devobj)
            for group in device:
                self.process_group(devobj, group)
                for capability in group:
                    self.process_capability(devobj, group, capability)
            if devobj:
                if devobj.parent != "root" and (devobj.parent not in self.done):
                    if devobj.parent not in self.deferred:
                        self.deferred[devobj.parent] = []
                    self.deferred[devobj.parent].append(devobj)
                    self.process_new_deferred(devobj)
                else:
                    self.done[devobj.devid] = devobj
                    self.handle_device(devobj)
                    self.process_deferred()
        try:
            while self.deferred:
                deferred_len = len(self.deferred)
                self.process_deferred()
                if deferred_len == len(self.deferred):
                    raise DeferredDeviceError("%s devices still deferred: %s" %
                                              (deferred_len,
                                               self.deferred.keys()))
        finally:
            self.end_process()


def main(processor_class, device_handler_class, option_parser):
    """
    Main utility function

    Function to help instantiate a WurflProcessor class or subclass with
    additional command line options.

    @param processor_class: The WurflProcessor class or a subclass.
    @type processor_class: WurflProcessor
    @param device_handler_class: A reference to a subclass of DeviceHandler.
    @type device_handler_class: DeviceHandler
    @param option_parser: An instance of OptionParser. The dictionary from
                          this object will be passed to processor_class in
                          the keyword 'option'.
    @type option_parser: OptionParser.OptionParser
    """
    options, args = option_parser.parse_args()

    if args:
        wurflxml = args[0]
    else:
        print >> sys.stderr, op.get_usage()
        sys.exit(1)

    wurfl = processor_class(wurflxml, device_handler=device_handler_class,
                            options=options.__dict__)
    wurfl.process()


usage = "usage: %prog [options] WURFL_XML_FILE"
op = OptionParser(usage=usage)
op.add_option("-l", "--logfile", dest="logfile", default=sys.stderr,
              help="where to write log messages")


if __name__ == "__main__":
    main(WurflProcessor, None, op)
