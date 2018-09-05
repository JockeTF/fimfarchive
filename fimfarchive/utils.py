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
from functools import partial
from importlib_resources import read_binary, read_text
from typing import Any, Dict, Iterator, Optional, Type, TypeVar, Union

from tqdm import tqdm

from fimfarchive.flavors import Flavor
from fimfarchive.stories import Story


__all__ = (
    'Empty',
    'PersistedDict',
    'find_flavor',
    'tqdm',
)


F = TypeVar('F', bound=Flavor)


tqdm = partial(
    tqdm,
    ascii=True,
    leave=False,
    smoothing=0,
    ncols=72,
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


class PersistedDict(Dict[str, Any]):
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
        self.clear()
        self.update(self.default)

        if os.path.exists(self.path):
            with open(self.path, 'rt') as fobj:
                self.update(json.load(fobj))

    def save(self):
        """
        Saves data to file as JSON.
        """
        content = json.dumps(
            self,
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


class JayWalker:
    """
    Walker for JSON objects.
    """

    def walk(self, data) -> None:
        """
        Walks the attributes of a JSON object.

        Args:
            data: The object to walk.
        """
        iterator: Iterator

        if isinstance(data, dict):
            iterator = iter(data.items())
        elif isinstance(data, list):
            iterator = enumerate(data)
        else:
            return

        for key, value in iterator:
            self.handle(data, key, value)

    def handle(self, data, key, value) -> None:
        """
        Handles a single JSON entry.

        Args:
            data: The current object.
            key: The key of the entry.
            value: The value of the entry.
        """
        self.walk(value)


def find_flavor(story: Story, flavor: Type[F]) -> Optional[F]:
    """
    Searches for a flavor of a specific type.

    Args:
        story: The story to search in.
        flavor: The flavor type to find.

    Returns:
        A flavor of the desired type, or None.
    """
    for current in story.flavors:
        if isinstance(current, flavor):
            return current

    return None


class ResourceLoader:
    """
    Loads resources from a package.
    """

    def __init__(self, package: str, binary: bool = False) -> None:
        """
        Constructor.

        Args:
            package: The package to load from.
            binary: Set to return binary data.
        """
        self.package = package
        self.binary = binary

    def __call__(self, name: str, binary: bool = None) -> Union[str, bytes]:
        """
        Loads a package resource.

        Args:
            name: The name of the resource to load.
            binary: Set to return binary data.

        Returns:
            A resource as string or bytes.
        """
        if binary is None:
            binary = self.binary

        if binary:
            return read_binary(self.package, name)
        else:
            return read_text(self.package, name)
