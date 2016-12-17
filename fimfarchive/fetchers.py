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


from copy import deepcopy
import gc
from io import BytesIO
import json
import requests
from zipfile import ZipFile, BadZipFile

from fimfarchive.exceptions import InvalidStoryError, StorySourceError


class Fetcher:
    """
    Abstract base class for story fetchers.
    """

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
        raise NotImplementedError()

    def fetch(self, key):
        """
        Fetches story information.

        Args:
            key: Primary key of the story.

        Returns:
            Story: A new `Story` object.

        Raises:
            InvalidStoryError: If a valid story is not found.
            StorySourceError: If source does not return any data.
        """
        raise NotImplementedError()

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
    data_path = 'https://www.fimfiction.net/download_story.php'
    meta_path = 'https://www.fimfiction.net/api/story.php'

    def close(self):
        pass

    def get(self, url, **kwargs):
        """
        Performs an HTTP GET request.

        Args:
            url: Target of the HTTP request.
            **kwargs: HTTP query parameters.

        Returns:
            Response: A new `Response` object.

        Raises:
            StorySourceError: If the server does not return HTTP 200 OK.
        """
        try:
            response = requests.get(url, params=kwargs)
        except IOError as e:
            raise StorySourceError("Could not read from server.") from e

        if not response.ok:
            raise StorySourceError(
                "Server responded with HTTP {} {}."
                .format(response.status_code, response.reason)
            )

        return response

    def fetch_data(self, key):
        response = self.get(self.data_path, story=key, html=True)
        data = response.content

        if len(data) == 0:
            raise InvalidStoryError("Server returned empty response body.")

        if b'<a name=\'1\'></a><h3>' not in data:
            raise InvalidStoryError("Server did not return any chapters.")

        if not data.endswith(b'</html>'):
            raise StorySourceError("Server returned incomplete response.")

        return data

    def fetch_meta(self, key):
        response = self.get(self.meta_path, story=key)

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
            byte_index = self.archive.read('index.json')
        except KeyError as e:
            raise StorySourceError("Archive is missing the index.") from e
        except BadZipFile as e:
            raise StorySourceError("Archive is corrupt.") from e

        try:
            text_index = byte_index.decode()
        except UnicodeDecodeError as e:
            raise StorySourceError("Index is incorrectly encoded.") from e

        del byte_index
        gc.collect()

        try:
            self.index = json.loads(text_index)
        except ValueError as e:
            raise StorySourceError("Index is not valid JSON.") from e

        del text_index
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

            if 'Chapter1.html' not in story.namelist():
                raise InvalidStoryError("Story contains no chapters.")

        return data

    def fetch_meta(self, key):
        meta = self.lookup(key)
        return deepcopy(meta)
