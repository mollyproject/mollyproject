""" Filter to remove whitespace from input CSS """

from __future__ import absolute_import

import re

from pipeline.compressors import CompressorBase

class MollyCSSFilter(CompressorBase):
    
    _COMMENT_RE = re.compile(r'/\*.*?\*/')
    _WHITESPACE_RE = re.compile(r'[ \t\n\r]+')
    
    def compress_css(self, css):
        css = self._COMMENT_RE.sub('', css)
        css = self._WHITESPACE_RE.sub(' ', css)
        return css.strip()
