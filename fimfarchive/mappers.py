"""
Mappers for Fimfarchive.
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


import os


__all__ = (
    'Mapper',
    'StaticMapper',
    'StoryPathMapper',
)


class Mapper:
    """
    Callable which maps something to something else.
    """

    def __call__(self, *args, **kwargs):
        raise NotImplementedError()


class StaticMapper(Mapper):
    """
    Returns the supplied value for any call.
    """

    def __init__(self, value=None):
        self.value = value

    def __call__(self, *args, **kwargs):
        return self.value


class StoryPathMapper(Mapper):
    """
    Returns a key-based file path for a story.
    """

    def __init__(self, directory):
        self.directory = directory

    def __call__(self, story):
        directory = str(self.directory)
        key = str(story.key)

        return os.path.join(directory, key)
