import urllib2
import sys
import os.path
import imp

class AnyMethodRequest(urllib2.Request):
    def __init__(self, url, data=None, headers={}, origin_req_host=None, unverifiable=None, method=None):
        self.method = method and method.upper() or None
        urllib2.Request.__init__(self, url, data, headers, origin_req_host, unverifiable)

    def get_method(self):
        if not self.method is None:
            return self.method
        elif self.has_data():
            return "POST"
        else:
            return "GET"


def get_norm_sys_path():
    """
    Returns a normalised path that can be used for PYTHONPATH to recreate the
    path used for this invocation. 
    """

    sys_path = sys.path[:]

    # Find the path to the first package containing the settings module.
    # Once we have it, normalise it and add it to our sys_path if it isn't
    # already there.
    try:
        project_path = imp.find_module(os.environ['DJANGO_SETTINGS_MODULE'].split('.')[0])[1]
    except ImportError:
        project_path = os.path.dirname(imp.find_module('settings')[1])
    sys_path.insert(0, os.path.join(project_path, '..'))

    sys_path = [os.path.normpath(p) for p in sys_path if p != '']

    # Remove duplicates. This is O(n^2), but efficiency isn't too much of an
    # issue when n is small.
    sys_path = [p for i,p in enumerate(sys_path) if p not in sys_path[:i]]

    return sys_path