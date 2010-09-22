from __future__ import absolute_import

import re

from compress.filter_base import FilterBase

class MollyCSSFilter(FilterBase):
    _WHITESPACE_RE = re.compile(r'[ \t\n\r]+')
    def filter_css(self, css):
        return self._WHITESPACE_RE.sub(' ', css).strip()