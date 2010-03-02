import settings

class Applications(object):
    def __init__(self):
        self.applications = {}

    def __getattr__(self, name):
        try:
            return self.applications[name]
        except KeyError:
            self.applications[name] = settings.Application.get(name)
            return self.applications[name]
