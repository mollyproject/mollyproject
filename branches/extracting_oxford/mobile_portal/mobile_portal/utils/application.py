from django.utils.importlib import import_module

class Application(object):
    def __init__(self, app_name, app_connector):
        self.module = import_module(app_name)
        self.connector = import_module(app_connector)
        