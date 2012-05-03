from molly.conf.provider import Provider


class BaseTransitLineStatusProvider(Provider):
    
    def get_status(self):
        # Return a dictionary with a key of 'service_name', which is the human
        # readable name of the service this status provider describes, and the
        # 'line_statuses' key is a list of dictionaries, where the dictionaries
        # have keys of "line_id", "line_name", "status" and optional
        # "disruption_reason"
        return {}

from molly.apps.transport.providers.tfl import TubeStatusProvider
