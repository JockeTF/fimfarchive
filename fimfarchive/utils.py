"""
Various utilities.
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


import json
import os
import shutil
from collections import UserDict


__all__ = (
    'Empty',
    'PersistedDict',
)


class EmptyMeta(type):
    """
    Meta-class for Empty.
    """

    def __bool__(cls):
        return False


class Empty(metaclass=EmptyMeta):
    """
    Unique placeholder similar to `None`.
    """

    def __bool__(self):
        return False


class PersistedDict(UserDict):
    """
    Dictionary for simple persistance.
    """

    def __init__(self, path, default=dict()):
        """
        Constructor.

        Args:
            path: Location of the persistence file.
            default: Initial values for entries.
        """
        super().__init__()
        self.path = path
        self.temp = path + '~'
        self.default = default
        self.load()

    def load(self):
        """
        Loads data from file as JSON.
        """
        if os.path.exists(self.path):
            with open(self.path, 'rt') as fobj:
                self.data = json.load(fobj)
        else:
            self.data = dict()

        for k, v in self.default.items():
            if not k in self.data:
                self.data[k] = v

    def save(self):
        """
        Saves data to file as JSON.
        """
        content = json.dumps(
            self.data,
            indent=4,
            ensure_ascii=False,
            sort_keys=True,
        )

        if os.path.exists(self.path):
            shutil.copy(self.path, self.temp)

        with open(self.path, 'wt') as fobj:
            fobj.write(content)

        if os.path.exists(self.temp):
            os.remove(self.temp)
