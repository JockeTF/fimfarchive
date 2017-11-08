"""
Flavors for Fimfarchive.
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


from enum import Enum


__all__ = (
    'Flavor',
    'StorySource',
    'DataFormat',
    'MetaFormat',
    'MetaPurity',
    'UpdateStatus',
)


class Flavor(Enum):
    """
    Base class for flavors.
    """

    def __new__(cls, *args):
        """
        Automatically assigns an enum value.
        """
        value = len(cls.__members__) + 1
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

    def __repr__(self):
        """
        Custom representation for instances.
        """
        return "<flavor '{}.{}'>".format(
            type(self).__name__,
            getattr(self, 'name', None),
        )


class StorySource(Flavor):
    """
    Indicates from where a story was fetched.
    """
    FIMFICTION = ()
    FIMFARCHIVE = ()


class DataFormat(Flavor):
    """
    Indicates the file format of story data.
    """
    EPUB = ()
    FPUB = ()
    HTML = ()
    JSON = ()


class MetaFormat(Flavor):
    """
    Indicates the general structure of story meta.
    """
    ALPHA = ()
    BETA = ()


class MetaPurity(Flavor):
    """
    Indicates if story meta has been sanitized.
    """
    CLEAN = ()
    DIRTY = ()


class UpdateStatus(Flavor):
    """
    Indicates if and how a story has changed.
    """
    CREATED = ()
    REVIVED = ()
    UPDATED = ()
    DELETED = ()
