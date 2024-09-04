"""
Various utilities.
"""


#
# Fimfarchive, preserves stories from Fimfiction.
# Copyright (C) 2023  Joakim Soderlund
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
from importlib import import_module
from importlib.resources import files
from pathlib import Path
from typing import (
    cast, Any, Callable, Dict, Iterator,
    Optional, Set, Tuple, Type, TypeVar, Union,
)

from tqdm import tqdm as _tqdm

from fimfarchive.flavors import Flavor
from fimfarchive.stories import Story


__all__ = (
    'Empty',
    'PersistedDict',
    'ResourceLoader',
    'find_compressor',
    'find_flavor',
    'get_path',
    'tqdm',
)


ByteFunc = Callable[[bytes], bytes]
F = TypeVar('F', bound=Flavor)
T = TypeVar('T')


#
# Authors who have opted out of being archived.
#
# Please respect their wishes.
#

AUTHOR_BLACKLIST: Set[int] = {
    33094,
    135140,
    220118,
    242007,
    296868,
}

STORY_BLACKLIST: Set[int] = {
    316169,
    318201,
    413197,
    499134,
}

STORY_WHITELIST: Set[int] = set()


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


def find_compressor() -> Tuple[ByteFunc, ByteFunc]:
    """
    Searches for a fast compression module.

    Returns:
        A pair of compression functions.
    """
    for compressor in ('lz4.block', 'snappy', 'lzo'):
        try:
            module: Any = import_module(compressor)
            return module.compress, module.decompress
        except ImportError:
            pass

    dummy = cast(ByteFunc, lambda data: data)

    return dummy, dummy


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


def get_path(source: Union[None, Path, str]) -> Optional[Path]:
    """
    Creates a path from an object, if one is supplied.

    Args:
        source: Object to create a path from.

    Returns:
        A resolved path instance, or None.
    """
    if source is None:
        return None

    return Path(source).resolve()


def is_blacklisted(story: Story) -> bool:
    """
    Checks if a story has been blacklisted.

    Args:
        story: Instance to check.

    Returns:
        True if a story has been blacklisted.
    """
    story_id = int(story.meta['id'])
    author_id = int(story.meta['author']['id'])

    if story_id in STORY_WHITELIST:
        return False
    elif story_id in STORY_BLACKLIST:
        return True
    elif author_id in AUTHOR_BLACKLIST:
        return True
    else:
        return False


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

    def __call__(
            self,
            name: str,
            binary: Optional[bool] = None,
            ) -> Union[str, bytes]:
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

        package = files(self.package)
        resource = package.joinpath(name)

        if binary:
            return resource.read_bytes()
        else:
            return resource.read_text()


class tqdm(_tqdm):
    """
    Adds an ASCII progress bar to the iterable.
    """

    defaults = {
        'ascii': True,
        'leave': False,
        'smoothing': 0.0,
        'ncols': 72,
    }

    def __init__(self, *args, **kwargs):
        kwargs = {**self.defaults, **kwargs}
        return super().__init__(*args, **kwargs)
