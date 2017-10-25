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


import codecs
import gc
import json
from copy import deepcopy
from io import BytesIO
from zipfile import ZipFile, BadZipFile

from fimfarchive.exceptions import InvalidStoryError, StorySourceError
from fimfarchive.flavors import StorySource, DataFormat, MetaPurity

from .base import Fetcher


__all__ = (
    'FimfarchiveFetcher',
)


StreamReader = codecs.getreader('utf-8')


class FimfarchiveFetcher(Fetcher):
    """
    Fetcher for Fimfarchive.
    """
    prefetch_meta = True
    prefetch_data = True

    flavors = frozenset((
        StorySource.FIMFARCHIVE,
        DataFormat.EPUB,
        MetaPurity.CLEAN,
    ))

    def __init__(self, file):
        """
        Initializes a `FimfarchiveFetcher` instance.

        Args:
            file: Path or file-like object for a Fimfarchive release.

        Raises:
            StorySourceError: If no valid Fimfarchive release can be loaded.
        """
        self.is_open = False
        self.archive = None
        self.index = None

        try:
            self._init(file)
        except Exception:
            self.close()
            raise
        else:
            self.is_open = True

    def _init(self, file):
        """
        Internal initialization method.
        """
        try:
            self.archive = ZipFile(file)
        except IOError as e:
            raise StorySourceError("Could not read from file.") from e
        except BadZipFile as e:
            raise StorySourceError("Archive is not a valid ZIP-file.") from e

        try:
            with self.archive.open('index.json') as fobj:
                self.index = json.load(StreamReader(fobj))
        except KeyError as e:
            raise StorySourceError("Archive is missing the index.") from e
        except ValueError as e:
            raise StorySourceError("Index is not valid JSON.") from e
        except UnicodeDecodeError as e:
            raise StorySourceError("Index is incorrectly encoded.") from e
        except BadZipFile as e:
            raise StorySourceError("Archive is corrupt.") from e

        gc.collect()

    def close(self):
        self.is_open = False
        self.index = None

        if self.archive is not None:
            self.archive.close()
            self.archive = None

        gc.collect()

    def lookup(self, key):
        """
        Finds meta for a story in the index.

        Args:
            key: Primary key of the story.

        Returns:
            dict: A reference to the story's meta.

        Raises:
            InvalidStoryError: If story does not exist.
            StorySourceError: If archive is closed.
        """
        if not self.is_open:
            raise StorySourceError("Fetcher is closed.")

        key = str(key)

        if key not in self.index:
            raise InvalidStoryError("Story does not exist.")

        return self.index[key]

    def fetch_data(self, key):
        meta = self.lookup(key)

        if 'path' not in meta:
            raise StorySourceError("Index is missing a path value.")

        try:
            data = self.archive.read(meta['path'])
        except ValueError as e:
            raise StorySourceError("Archive is missing a file.") from e
        except BadZipFile as e:
            raise StorySourceError("Archive is corrupt.") from e

        with ZipFile(BytesIO(data)) as story:
            if story.testzip() is not None:
                raise StorySourceError("Story is corrupt.")

        return data

    def fetch_meta(self, key):
        meta = self.lookup(key)
        return deepcopy(meta)
