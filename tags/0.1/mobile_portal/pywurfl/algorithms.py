# pywurfl Algorithms - Wireless Universal Resource File UA search algorithms
# Copyright (C) 2006-2009 Armand Lynch
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation; either version 2.1 of the License, or (at your
# option) any later version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#
# Armand Lynch <lyncha@users.sourceforge.net>

__doc__ = \
"""
pywurfl search algorithms
"""

import re

from pywurfl.exceptions import DeviceNotFound


__author__ = "Armand Lynch <lyncha@users.sourceforge.net>"
__copyright__ = "Copyright 2006-2009, Armand Lynch"
__license__ = "LGPL"
__url__ = "http://celljam.net/"


class Algorithm(object):
    """
    Base class for all pywurfl search algorithms
    """
    def __call__(self, ua, devices):
        """
        Every pywurfl algorithm class must define a __call__ method.

        @param ua: The user agent
        @type ua: string
        @param devices: The devices object to search
        @type devices: Devices
        @rtype: Device
        """
        raise NotImplementedError


try:
    import Levenshtein

    class JaroWinkler(Algorithm):
        """
        Jaro-Winkler Search Algorithm
        """

        def __init__(self, accuracy=1.0, weight=0.05):
            """
            @param accuracy: The tolerance that the Jaro-Winkler algorithm will
                             use to determine if a user agent matches
                             0.0 <= accuracy <= 1.0
            @type accuracy: float
            @param weight: The prefix weight is inverse value of common prefix
                           length sufficient to consider the strings
                           'identical' (excerpt from the Levenshtein module
                           documentation).
            @type weight: float
            """

            self.accuracy = accuracy
            self.weight = weight

        def __call__(self, ua, devices):
            """
            @param ua: The user agent
            @type ua: string
            @param devices: The devices object to search
            @type devices: Devices
            @rtype: Device
            @raises pywurfl.DeviceNotFound
            """
            match = max((Levenshtein.jaro_winkler(x, ua, self.weight), x) for
                        x in devices.devuas)
            if match[0] >= self.accuracy:
                return devices.devuas[match[1]]
            else:
                raise DeviceNotFound(ua)


    class LevenshteinDistance(Algorithm):
        """
        Levenshtein distance Search Algorithm
        """

        def __call__(self, ua, devices):
            """
            @param ua: The user agent
            @type ua: string
            @param devices: The devices object to search
            @type devices: Devices
            @rtype: Device
            """

            match = max((Levenshtein.distance(ua, x), x) for x in
                        devices.devuas)
            return devices.devuas[match[1]]

except ImportError:
    pass


class Tokenizer(Algorithm):
    """
    Tokenizer Search Algorithm
    """
    tokenize_chars = ('/', '.', ',', ';', '-', '_', ' ', '(', ')')
    base_regex = '[\\'+'\\'.join(tokenize_chars)+']*'

    def __init__(self, devwindow=30):
        """
        @param devwindow: If more than devwindow user agents match,
                          return empty device.
        @type devwindow: integer
        """
        self.devwindow = devwindow

    def _tokenize(self, s):
        """
        @param s: The user agent to tokenize
        @type s: string
        """
        for d in self.tokenize_chars:
            s = s.replace(d, ' ')
        return [re.escape(x) for x in s.split()]

    def __call__(self, ua, devices):
        """
        @param ua: The user agent
        @type ua: string
        @param devices: The devices object to search
        @type devices: Devices
        @rtype: Device
        """
        uas = devices.devuas.keys()
        tokens = self._tokenize(ua)
        regex = ''
        for t in tokens:
            if regex:
                regex += self.base_regex + t
            else:
                regex += t

            regex2 = regex + '.*'

            uare = re.compile(regex2, re.I)
            uas2 = [x for x in uas if uare.match(x)]

            # If the last regex didn't produce any matches and more than
            # devwindow devices were matched before, return a generic device.
            # Else, there is a device that "looks" like some others so return
            # the first one.
            if len(uas2) == 0 and len(uas) > self.devwindow:
                return devices.devids['generic']
            elif len(uas2) == 0 and len(uas) <= self.devwindow:
                #uas.sort()
                return devices.devuas[uas[0]]

            # We found one good looking match
            if len(uas2) == 1:
                #uas2.sort()
                return devices.devuas[uas2[0]]

            # We've got matches so search some more
            uas = uas2

        # We've got some matches but we ran out of tokens so search with.
        # If we matched more than devwindow, return a generic device.
        # Else we've got some devices within the devwindow so return the first
        # one.
        if len(uas2) > self.devwindow:
            return devices.devids['generic']
        else:
            #uas2.sort()
            return devices.devuas[uas2[0]]
