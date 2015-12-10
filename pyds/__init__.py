# vim: filetype=python3 tabstop=2 expandtab

# pyds
# Copyright (C) 2015 Jashandeep Sohi
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""
Read, write and manipulate NASA's PDS (Planetary Data System) labels.
"""

__version__ = "0.3.0"

from .values import *
from .statements import *
from .parser import *

__all__ = values.__all__ + statements.__all__ + parser.__all__
