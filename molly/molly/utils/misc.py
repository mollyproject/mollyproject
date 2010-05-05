import urllib2

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

