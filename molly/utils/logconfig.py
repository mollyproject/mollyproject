import logging
import inspect
import traceback
import hashlib
import pprint
import datetime
import sys

from django.http import HttpRequest
from django.conf import settings

from . import send_email

class StreamHandler(logging.StreamHandler):
    def filter(self, record):
        return record.name != 'molly.stats.requests'

class EmailHandler(logging.Handler):
    _NOT_EXTRA = (
        'args', 'created', 'exc_info', 'exc_text', 'filename', 'funcName',
        'getMessage', 'levelname', 'levelno', 'lineno', 'msg', 'message',
        'module', 'msecs', 'name', 'pathname', 'process', 'processName',
        'relativeCreated', 'thread', 'threadName'
    )
    
    class conf:
        from_email = settings.SERVER_EMAIL if hasattr(settings, 'SERVER_EMAIL') else 'molly@localhost'
    
    def filter(self, record):
        return record.name != 'molly.stats.requests'
    
    def emit(self, record):

        # Recurse up the call stack to find the request that was being
        # processed when this log message was emitted. If none is found,
        # request is set to None. Functional, but possibly hacky.
        # Don't do this at home, kids.
        for frame in inspect.getouterframes(inspect.currentframe()):
            request = frame[0].f_locals.get('request', None)
            if isinstance(request, HttpRequest):
                break

        extra = {}
        for key in dir(record):
            if key.startswith('_') or key in self._NOT_EXTRA:
                continue
            extra[key] = '    ' + pprint.pformat(getattr(record, key), width=75).replace('\n', '\n    ')

        context = {
            'record': record,
            'level_name': logging._levelNames.get(record.levelno, "L%s" % record.levelno),
            'level_stars': '*' * (record.levelno // 10),
            'priority': 'urgent' if record.levelno >= 40 else 'normal',
            'extra': extra,
            'created': datetime.datetime.fromtimestamp(record.created)
        }

        # hash is a hash of some key details of the log record, specifically
        # the log level, the (unformatted) message, and where it was emitted.
        # If there is an attached exception we take the locations of the first
        # two elements of the traceback.
        hash = hashlib.sha1()
        hash.update('%d' % record.levelno)
        hash.update(str(record.msg))
        hash.update('%d%s' % (record.lineno, record.pathname))


        if record.exc_info:
            exc_type, exc_value, exc_traceback = record.exc_info
            hash.update('%s%s' % (exc_type.__module__, exc_type.__name__))
            context['traceback'] = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            for i in range(2):
                hash.update('%d%s' % (exc_traceback.tb_lineno, exc_traceback.tb_frame.f_code.co_filename))
                exc_traceback = exc_traceback.tb_next if exc_traceback.tb_next is not None else exc_traceback

        context['hash'] = hash.hexdigest()[:8]

        send_email(request, context, 'utils/log_record.eml', cls=self)

def configure_logging(conf):
    
    # We only care about stuff Molly complains about at this point
    logger = logging.getLogger('molly')
    
    if settings.DEBUG:
        # This checks if we're using the dev server - can't log to stderr
        # in WSGI, even in debug mode
        # http://stackoverflow.com/questions/1291755/how-can-i-tell-whether-my-django-application-is-running-on-development-server-or
        # can't do it the preferred way however, as we don't have access to a
        # request object here
        if sys.argv[1] == 'runserver':
            
            # when in debug mode, log Molly at debug level to stdout
            handler = StreamHandler()
            logger.setLevel(logging.DEBUG)
            
            # Log everyone else at info level
            logging.getLogger().setLevel(logging.INFO)
        else:
            return
    else:
        
        # When not in debug mode, e-mail warnings and above to admins
        handler = EmailHandler()
        handler.setLevel(logging.WARNING)
    logger.addHandler(handler)