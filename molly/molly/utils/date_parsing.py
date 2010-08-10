from __future__ import absolute_import

import email.utils
from datetime import datetime, timedelta, tzinfo

def rfc_2822_datetime(value):
    time_tz = email.utils.parsedate_tz(value)

    class tz(tzinfo):
        def utcoffset(self, dt):
            return timedelta(seconds=time_tz[9])
        def dst(self, dt):
            return timedelta(0)
        def __repr__(self):
            return "%02d%02d" % (time_tz[9]//3600, (time_tz[9]//60) % 60)

    return datetime(*(time_tz[:6] + (0, tz())))
