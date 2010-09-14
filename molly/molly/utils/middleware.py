import logging

from django.http import Http404
from django.core.exceptions import ImproperlyConfigured, PermissionDenied

logger = logging.getLogger("molly.utils.middleware")

class ErrorHandlingMiddleware(object):
    def process_exception(self, request, exception):
        if isinstance(exception, Http404):
            pass
        if isinstance(exception, PermissionDenied):
            pass
        elif isinstance(exception, ImproperlyConfigured):
            logger.critical("Site improperly configured", exc_info=True)
        else:
            logger.exception("View raised an uncaught error")