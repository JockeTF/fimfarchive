"""
Directory fetcher.
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
from itertools import chain
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, Optional, Set, Sized, Union

from fimfarchive.exceptions import InvalidStoryError, StorySourceError
from fimfarchive.flavors import Flavor
from fimfarchive.stories import Story
from fimfarchive.utils import get_path

from .base import Fetcher


__all__ = (
    'DirectoryFetcher',
)


class DirectoryFetcher(Iterable[Story], Sized, Fetcher):
    """
    Fetches stories from file system.
    """
    prefetch_meta = False
    prefetch_data = False

    def __init__(
            self,
            meta_path: Union[Path, str] = None,
            data_path: Union[Path, str] = None,
            flavors: Iterable[Flavor] = tuple(),
            ) -> None:
        """
        Constructor.

        Args:
            meta: The directory for story meta.
            data: The directory for story data.
            flavors: The flavors to add to stories.
        """
        self.meta_path = get_path(meta_path)
        self.data_path = get_path(data_path)
        self.length: Optional[int] = None
        self.flavors = frozenset(flavors)

    def iter_path_keys(self, path: Optional[Path]) -> Iterator[int]:
        """
        Yields all story keys found in the specified directory.

        Args:
            path: Path to the directory.

        Returns:
            An iterator over story key.

        Raises:
            StorySourceError: If the path is invalid.
        """
        if path is None:
            return

        if not path.is_dir():
            raise StorySourceError(f"Path is not a directory: {path}")

        for item in Path(path).iterdir():
            if not item.is_file():
                raise StorySourceError(f"Path is not a file: {item}")

            if not item.name.isdigit():
                raise StorySourceError(f"Name is not a digit: {item}")

            yield int(item.name)

    def list_keys(self) -> Set[int]:
        """
        Lists all available story keys.

        Returns:
            An unordered set of story keys.

        Raises:
            StorySourceError: If any path is invalid.
        """
        meta_keys = self.iter_path_keys(self.meta_path)
        data_keys = self.iter_path_keys(self.data_path)

        return set(chain(meta_keys, data_keys))

    def __len__(self) -> int:
        """
        Returns the total number of stories in the directories.
        """
        if self.length is None:
            self.length = len(self.list_keys())

        return self.length

    def __iter__(self) -> Iterator[Story]:
        """
        Yields all stories in the directories, ordered by ID.
        """
        for key in sorted(self.list_keys()):
            yield self.fetch(key)

    def read_file(self, path: Path) -> bytes:
        """
        Reads file data for the path.

        Args:
            path: The path to read from.

        Returns:
            The file contents as bytes.

        Raises:
            InvalidStoryError: If the file does not exist.
            StorySourceError: If the file could not be read.
        """
        try:
            return path.read_bytes()
        except FileNotFoundError as e:
            raise InvalidStoryError("File does not exist.") from e
        except Exception as e:
            raise StorySourceError("Unable to read file.") from e

    def fetch_data(self, key: int) -> bytes:
        if self.data_path is None:
            raise StorySourceError("Data path is undefined.")

        path = self.data_path / str(key)
        raw = self.read_file(path)

        return raw

    def fetch_meta(self, key: int) -> Dict[str, Any]:
        if self.meta_path is None:
            raise StorySourceError("Meta path is undefined.")

        path = self.meta_path / str(key)
        raw = self.read_file(path)

        return json.loads(raw.decode())
