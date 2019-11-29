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
import marshal
from io import BufferedReader
from multiprocessing import Pool
from typing import (
    cast, Any, Callable, Dict, IO, Iterable, Iterator,
    Mapping, Optional, Sized, Tuple, Union,
)
from zipfile import ZipFile, BadZipFile

from jmespath import compile as jmes

from fimfarchive.exceptions import InvalidStoryError, StorySourceError
from fimfarchive.flavors import StorySource, DataFormat, MetaPurity
from fimfarchive.stories import Story
from fimfarchive.utils import find_compressor

from .base import Fetcher


__all__ = (
    'FimfarchiveFetcher',
)


BUFFER_SIZE = 8_000_000
PATH = jmes('archive.path || path')


compress, decompress = find_compressor()
serialize = cast(Callable[[Dict[str, Any]], bytes], marshal.dumps)
deserialize = cast(Callable[[bytes], Dict[str, Any]], marshal.loads)


class Index(Mapping[int, Dict[str, Any]]):
    """
    Mapping from story key to meta.
    """

    def close(self) -> None:
        """
        Closes the index, if necessary.
        """

    def load(self, source: IO[bytes]) -> Iterator[Tuple[int, bytes]]:
        """
        Yields index items from a byte stream.

        Args:
            source: The stream to read from.

        Returns:
            An iterable over index items.

        Raises:
            StorySourceError: If the stream is malformed.
        """
        reader = BufferedReader(source, BUFFER_SIZE)  # type: ignore

        with Pool() as pool:
            parts = (part for part in reader if 2 < len(part))
            mapper = pool.imap(self.parse, parts, 1024)

            for key, value in mapper:
                if key < 0:
                    raise StorySourceError(value.decode())
                else:
                    yield key, value

    @staticmethod
    def parse(pair: bytes) -> Tuple[int, bytes]:
        """
        Converts a JSON key-value pair to Marshal.

        Args:
            pair: JSON key-value pair.

        Returns:
            Marshal key-value pair.
        """
        try:
            key, meta = pair.split(b':', 1)
            key = key.strip(b'\n\r\t "')
            meta = meta.strip(b'\n\r\t ,')
        except Exception as e:
            return -1, f"Unknown parser error: {e}".encode()

        if meta[0] != 123 or meta[-1] != 125:
            return -1, f"Malformed JSON object for {key!r}.".encode()

        try:
            return int(key), serialize(json.loads(meta.decode()))
        except UnicodeDecodeError as e:
            return -1, f"Incorrectly encoded index: {e}".encode()
        except ValueError as e:
            return -1, f"Malformed meta for {key!r}: {e}".encode()


class MemoryIndex(Index):
    """
    In-memory mapping from story key to meta.
    """

    def __init__(self, stream: IO[bytes]) -> None:
        self.data = {k: compress(v) for k, v in self.load(stream)}

    def __getitem__(self, key: int) -> Dict[str, Any]:
        return deserialize(decompress(self.data[key]))

    def __contains__(self, item) -> bool:
        return item in self.data

    def __iter__(self) -> Iterator[int]:
        return iter(self.data)

    def __len__(self) -> int:
        return len(self.data)

    def close(self):
        self.data.clear()


class FimfarchiveFetcher(Iterable[Story], Sized, Fetcher):
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
        self.index: Index
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
                self.index = MemoryIndex(fobj)
        except KeyError as e:
            raise StorySourceError("Archive is missing the index.") from e
        except BadZipFile as e:
            raise StorySourceError("Archive is corrupt.") from e

        self.paths = dict()
        self.is_open = True

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
        path = self.paths.get(key)

        if path is not None:
            return path

        meta = self.fetch_meta(key)
        path = PATH.search(meta)

        if path is not None:
            return path

        raise StorySourceError("Missing story path")

    def close(self) -> None:
        self.is_open = False

        if hasattr(self, 'archive'):
            self.archive.close()

        if hasattr(self, 'index'):
            self.index.close()

        if hasattr(self, 'paths'):
            self.paths.clear()

    def fetch_meta(self, key: int) -> Dict[str, Any]:
        key = self.validate(key)
        meta = self.index[key]
        actual = meta.get('id')

        if key != actual:
            raise StorySourceError(f"Invalid ID for {key}: {actual}")

        try:
            archive = meta.get('archive', meta)
            self.paths[key] = archive['path']
        except KeyError:
            pass

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
