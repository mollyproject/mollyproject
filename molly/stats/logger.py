import logging, os.path
from django.conf import settings

class AccessHandler(logging.Handler):
    BOT_UAS = [
        'gsa-crawler', 'slurp', 'googlebot', 'msnbot', 'spider', 'crawl',
    ]
    
    def __init__(self, *args, **kwargs):
        logging.Handler.__init__(self, *args, **kwargs)
        
        access_filename = os.path.join(settings.LOG_DIR, 'access')
        error_filename = os.path.join(settings.LOG_DIR, 'access_error')
        bot_filename = os.path.join(settings.LOG_DIR, 'access_bot')

        if not os.path.exists(access_filename):
            open(access_filename, 'w').close()
        if not os.path.exists(bot_filename):
            open(bot_filename, 'w').close()
            
        formatter = logging.Formatter("""\
%(ip_address)s %(requested)s %(referer)r %(full_path)r %(session_key)s \
%(user_agent)r %(device_id)s %(response_time).5f \
%(view_name)r %(status_code)d %(redirect_to)r\
""")
            
        error_formatter = logging.Formatter("""\
%(ip_address)s %(requested)s %(referer)r %(full_path)r %(session_key)s \
%(user_agent)r %(device_id)s %(response_time).5f \
%(view_name)r %(status_code)d %(redirect_to)r\n%(traceback)s\n
""")
            
        self.access_handler = logging.FileHandler(access_filename)
        self.bot_handler = logging.FileHandler(bot_filename)
        self.error_handler = logging.FileHandler(error_filename)
        
        self.access_handler.setLevel(logging.INFO)
        self.bot_handler.setLevel(logging.INFO)
        self.access_handler.setFormatter(formatter)
        self.bot_handler.setFormatter(formatter)
        self.error_handler.setLevel(logging.INFO)
        self.error_handler.setFormatter(error_formatter)
        
        
        
    def emit(self, record):
        print dir(record)
        print record.exc_info
        print record.exc_text
        
        if hasattr(record, 'traceback'):
            self.error_handler.emit(record)
            return
            
        ua = record.user_agent.lower()
        for bot_ua in AccessHandler.BOT_UAS:
            if bot_ua in ua:
                self.bot_handler.emit(record)
                break
        else:
            self.access_handler.emit(record)


def config_logging():
    logger = logging.getLogger('mobile_portal.stats.requests')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(AccessHandler())
    