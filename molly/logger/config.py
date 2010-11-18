import logging, sys, os.path, logging.handlers

def initialise_logging():


    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    os.environ['DJANGO_SETTINGS_MODULE'] = 'mobile_portal.settings'
    
    from django.conf import settings
    
    for app_name in settings.INSTALLED_APPS:
        log_module_name = '%s.logger' % app_name
        try:
            mod = __import__(log_module_name, globals(), locals(), ['config_logging'], -1)
            config_logging = mod.config_logging
        except (ImportError, AttributeError):
            pass
        else:
            config_logging()
        

    handler = logging.StreamHandler(sys.stdout)
    logger = logging.getLogger()
    handler.setLevel(logging.DEBUG)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

