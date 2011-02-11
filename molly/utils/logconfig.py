import logging, inspect, traceback, hashlib, pprint, datetime

from django.http import HttpRequest
from django.conf import settings

from . import send_email

class EmailHandler(logging.Handler):
    _NOT_EXTRA = (
        'args', 'created', 'exc_info', 'exc_text', 'filename', 'funcName',
        'getMessage', 'levelname', 'levelno', 'lineno', 'msg', 'message',
        'module', 'msecs', 'name', 'pathname', 'process', 'processName',
        'relativeCreated', 'thread', 'threadName'
    )
    
    class conf:
        from_email = settings.SERVER_EMAIL if hasattr(settings, 'SERVER_EMAIL') else 'molly@localhost'
    
    def emit(self, record):
        if record.name == 'molly.stats.requests':
            return

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
    if settings.DEBUG:
        return

    logger = logging.getLogger()
    
    handler = EmailHandler()
    handler.setLevel(logging.WARNING)
    logger.addHandler(handler)