"""
Story fetchers.
"""


#
# Fimfarchive, preserves stories from Fimfiction.
# Copyright (C) 2015  Joakim Soderlund
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#


from .base import Fetcher
from .directory import DirectoryFetcher
from .fimfarchive import FimfarchiveFetcher
from .fimfiction import FimfictionFetcher
from .fimfiction2 import Fimfiction2Fetcher


__all__ = (
    'Fetcher',
    'DirectoryFetcher',
    'FimfarchiveFetcher',
    'FimfictionFetcher',
    'Fimfiction2Fetcher',
)
