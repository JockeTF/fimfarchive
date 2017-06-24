"""
Fetchers for Fimfarchive.
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

import requests

from fimfarchive.exceptions import InvalidStoryError, StorySourceError
from fimfarchive.flavors import StorySource, DataFormat, MetaPurity
from fimfarchive.stories import Story


__all__ = (
    'Fetcher',
    'FimfictionFetcher',
    'FimfarchiveFetcher',
)


StreamReader = codecs.getreader('utf-8')


class Fetcher:
    """
    Abstract base class for story fetchers.
    """
    prefetch_meta = False
    prefetch_data = False

    flavors = frozenset()

    def __enter__(self):
        """
        Returns self for use in with statements.
        """
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Closes the fetcher on exit in with statements.
        """
        self.close()

    def close(self):
        """
        Closes file descriptors and frees memory.
        """
        pass

    def fetch(self, key, prefetch_meta=None, prefetch_data=None):
        """
        Fetches story information.

        Args:
            key: Primary key of the story.
            prefetch_meta: Force prefetching of meta.
            prefetch_data: Force prefetching of data.

        Returns:
            Story: A new `Story` object.

        Raises:
            InvalidStoryError: If a valid story is not found.
            StorySourceError: If source does not return any data.
        """
        if prefetch_meta is None:
            prefetch_meta = self.prefetch_meta

        if prefetch_meta:
            meta = self.fetch_meta(key)
        else:
            meta = None

        if prefetch_data is None:
            prefetch_data = self.prefetch_data

        if prefetch_data:
            data = self.fetch_data(key)
        else:
            data = None

        return Story(key, self, meta, data, self.flavors)

    def fetch_data(self, key):
        """
        Fetches story content data.

        Args:
            key: Primary key of the story.

        Returns:
            bytes: Story content data.

        Raises:
            InvalidStoryError: If a valid story is not found.
            StorySourceError: If source does not return any data.
        """
        raise NotImplementedError()

    def fetch_meta(self, key):
        """
        Fetches story meta information.

        Args:
            key: Primary key of the story.

        Returns:
            dict: Story meta information.

        Raises:
            InvalidStoryError: If a valid story is not found.
            StorySourceError: If source does not return any data.
        """
        raise NotImplementedError()


class FimfictionFetcher(Fetcher):
    """
    Fetcher for Fimfiction.
    """
    prefetch_meta = True
    prefetch_data = False

    data_path = 'https://www.fimfiction.net/story/download/{}/html'
    meta_path = 'https://www.fimfiction.net/api/story.php?story={}'

    flavors = frozenset((
        StorySource.FIMFICTION,
        DataFormat.HTML,
        MetaPurity.DIRTY,
    ))

    def get(self, url):
        """
        Performs an HTTP GET request.

        Args:
            url: Target of the HTTP request.

        Returns:
            Response: A new `Response` object.

        Raises:
            InvalidStoryError: If access to the resource was denied.
            StorySourceError: If the request fails for any other reason.
        """
        try:
            response = requests.get(url, timeout=60)
        except OSError as e:
            raise StorySourceError("Could not read from server.") from e

        if response.status_code == 403:
            raise InvalidStoryError("Access to resource was denied.")

        if not response.ok:
            raise StorySourceError(
                "Server responded with HTTP {} {}."
                .format(response.status_code, response.reason)
            )

        return response

    def fetch_data(self, key):
        url = self.data_path.format(key)
        response = self.get(url)
        data = response.content

        if len(data) == 0:
            raise InvalidStoryError("Server returned empty response body.")

        if b'<h1><a name=\'1\'></a>' not in data:
            raise InvalidStoryError("Server did not return any chapters.")

        if not data.endswith(b'</html>'):
            raise StorySourceError("Server returned incomplete response.")

        return data

    def fetch_meta(self, key):
        url = self.meta_path.format(key)
        response = self.get(url)

        try:
            meta = response.json()
        except ValueError as e:
            raise StorySourceError("Server did not return valid JSON.") from e

        if 'error' in meta:
            message = meta['error']

            if message == 'Invalid story id':
                raise InvalidStoryError("Story does not exist.")
            else:
                raise StorySourceError(message)

        if 'story' not in meta:
            raise StorySourceError("Server did not return a story object.")

        return meta['story']


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
        except:
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
