"""
Fimfarchive fetcher.
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
from typing import cast, Any, Dict, IO, Iterator, Optional, Tuple, Union
from zipfile import ZipFile, BadZipFile

from boltons.cacheutils import LRU
from jmespath import compile as jmes

from fimfarchive.exceptions import InvalidStoryError, StorySourceError
from fimfarchive.flavors import StorySource, DataFormat, MetaPurity
from fimfarchive.stories import Story
from fimfarchive.utils import Empty

from .base import Fetcher


__all__ = (
    'FimfarchiveFetcher',
)


PATH = jmes('archive.path || path')


class FimfarchiveFetcher(Fetcher):
    """
    Fetcher for Fimfarchive.
    """
    prefetch_meta = True
    prefetch_data = False

    flavors = frozenset((
        StorySource.FIMFARCHIVE,
        DataFormat.EPUB,
        MetaPurity.CLEAN,
    ))

    def __init__(self, source: Union[str, IO[bytes]]) -> None:
        """
        Constructor.

        Args:
            source: Path or file-like object for a Fimfarchive release.

        Raises:
            StorySourceError: If no valid Fimfarchive release can be loaded.
        """
        self.archive: ZipFile
        self.index: Dict[int, str]
        self.paths: Dict[int, str]
        self.is_open: bool = False

        try:
            self.initialize(source)
        except Exception:
            self.close()
            raise

    def initialize(self, source: Union[str, IO[bytes]]) -> None:
        """
        Internal initialization method.

        Args:
            source: Path or file-like object for a Fimfarchive release.

        Raises:
            StorySourceError: If no valid Fimfarchive release can be loaded.
        """
        try:
            self.archive = ZipFile(source)
        except IOError as e:
            raise StorySourceError("Could not read from source.") from e
        except BadZipFile as e:
            raise StorySourceError("Source is not a valid ZIP-file.") from e

        try:
            with self.archive.open('index.json') as fobj:
                self.index = dict(self.load_index(fobj))
        except KeyError as e:
            raise StorySourceError("Archive is missing the index.") from e
        except BadZipFile as e:
            raise StorySourceError("Archive is corrupt.") from e

        self.paths = LRU()
        self.is_open = True

    def load_index(self, source: IO[bytes]) -> Iterator[Tuple[int, str]]:
        """
        Yields unparsed index items from a byte stream.

        Args:
            source: The stream to read from.

        Returns:
            An iterable over index items.

        Raises:
            StorySourceError: If an item is malformed.
        """
        for part in source:
            if len(part) < 3:
                continue

            try:
                line = part.decode().strip()
            except UnicodeDecodeError as e:
                raise StorySourceError("Incorrectly encoded index.") from e

            key, meta = line.split(':', 1)
            key = key.strip(' "')
            meta = meta.strip(' ,')

            if meta[0] != '{' or meta[-1] != '}':
                raise StorySourceError(f"Malformed index meta: {meta}")

            try:
                yield int(key), meta
            except ValueError as e:
                raise StorySourceError(f"Malformed index key: {key}") from e

    def __len__(self) -> int:
        """
        Returns the total number of stories in the archive.
        """
        return len(self.index)

    def __iter__(self) -> Iterator[Story]:
        """
        Yields all stories in the archive, ordered by ID.
        """
        for key in sorted(self.index.keys()):
            yield self.fetch(key)

    def validate(self, key: int) -> int:
        """
        Ensures that the key matches a valid story

        Args:
            key: Primary key of the story.

        Returns:
            The key as cast to an int.

        Raises:
            InvalidStoryError: If a valid story is not found.
            StorySourceError: If the fetcher is closed.
        """
        key = int(key)

        if not self.is_open:
            raise StorySourceError("Fetcher is closed.")

        if key not in self.index:
            raise InvalidStoryError(f"No such story: {key}")

        return key

    def fetch_path(self, key: int) -> Optional[str]:
        """
        Fetches the archive path of a story.

        Args:
            key: Primary key of the story.

        Returns:
            A path to the story, or None.

        Raises:
            InvalidStoryError: If a valid story is not found.
            StorySourceError: If the fetcher is closed.
        """
        key = self.validate(key)
        path = self.paths.get(key, Empty)

        if path is not Empty:
            return cast(Optional[str], path)

        meta = self.fetch_meta(key)
        return PATH.search(meta)

    def close(self) -> None:
        self.is_open = False

        if hasattr(self, 'archive'):
            self.archive.close()

        if hasattr(self, 'index'):
            self.index.clear()

        if hasattr(self, 'paths'):
            self.paths.clear()

    def fetch_meta(self, key: int) -> Dict[str, Any]:
        key = self.validate(key)
        raw = self.index[key]

        try:
            meta = json.loads(raw)
        except ValueError as e:
            raise StorySourceError(f"Malformed meta for {key}: {raw}") from e

        actual = meta.get('id')

        if key != actual:
            raise StorySourceError(f"Invalid ID for {key}: {actual}")

        self.paths[key] = PATH.search(meta)

        return meta

    def fetch_data(self, key: int) -> bytes:
        key = self.validate(key)
        path = self.fetch_path(key)

        if not path:
            raise StorySourceError(f"Missing path attribute for {key}.")

        try:
            data = self.archive.read(path)
        except ValueError as e:
            raise StorySourceError(f"Missing file for {key}: {path}") from e
        except BadZipFile as e:
            raise StorySourceError(f"Corrupt file for {key}: {path}") from e

        return data
