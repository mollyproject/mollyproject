""" Filter to remove whitespace from input CSS """

from __future__ import absolute_import

import re

from compress.filter_base import FilterBase

class MollyCSSFilter(FilterBase):
    _COMMENT_RE = re.compile(r'/\*.*?\*/')
    _WHITESPACE_RE = re.compile(r'[ \t\n\r]+')
    def filter_css(self, css):
        css = self._COMMENT_RE.sub('', css)
        css = self._WHITESPACE_RE.sub(' ', css)
        return css.strip()
