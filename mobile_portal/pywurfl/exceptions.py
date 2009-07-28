# pywurfl Exceptions
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
Exception Classes
"""

__author__ = "Armand Lynch <lyncha@users.sourceforge.net>"
__copyright__ = "Copyright 2006-2009, Armand Lynch"
__license__ = "LGPL"
__url__ = "http://celljam.net/"


class WURFLException(Exception):
    """
    pywurfl base exception class.
    """
    pass


class ExistsException(WURFLException):
    """
    General exception class

    Raised when an operation should not continue if an object exists.
    """


class DeviceNotFound(WURFLException):
    """
    Device Not Found exception class

    Raised when pywurfl cannot find a device by using either select_*
    API functions.
    """
    pass


class ActualDeviceRootNotFound(WURFLException):
    """
    Actual Device Root Not Found exception class

    Raised when pywurfl cannot find an actual device root by using either
    select_* API functions.
    """
    pass

