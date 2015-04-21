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

from distutils.core import setup
from pyds import __version__, __doc__

if __name__ == "__main__":
  setup(
    name = "pyds",
    version = __version__,
    description = __doc__,
    author = "Jashandeep Sohi",
    author_email = "jashandeep.s.sohi@gmail.com",
    url = "https://github.com/jashandeep-sohi/pyds",
    license = "GPLv3",
    py_modules = ["pyds"]
  )

