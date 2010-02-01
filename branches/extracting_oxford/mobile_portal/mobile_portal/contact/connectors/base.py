class BaseContactConnector(object):
    """
    Base class for all contact connectors.
    """
    
    def __init__(self, *args, **kwargs):
        pass
        
    def search(self, sessionkey, cleaned_data):
        raise NotImplementedError
        
class ContactConnectorException(Exception):
    def __init__(self, msg):
        self.msg = msg
    
class ServiceUnavailableException(ContactConnectorException):
    def __init__(self):
        self.msg = 'Sorry; there was a temporary issue retrieving results.' +
                   ' Please try again shortly.'
    
