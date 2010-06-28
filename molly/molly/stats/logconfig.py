import logging

from .models import Hit

class StatisticsHandler(logging.Handler):
    def emit(self, record):
        hit = Hit(
            session_key = record.session_key,
            user_agent = record.user_agent,
            device_id = record.device_id,
            ip_address = record.ip_address,
            referer = record.referer,
            full_path = record.full_path,
            requested = record.requested,
            response_time = record.response_time,
            local_name = record.local_name,
            view_name = record.view_name,
            status_code = record.status_code,
            redirect_to = record.redirect_to,
            traceback = getattr(record, 'traceback', None),
        )
        hit.save()

def configure_logging(conf):
    if getattr(conf, 'log_to_database', True):
       logger = logging.getLogger('molly.stats.requests')
       logger.addHandler(StatisticsHandler())

