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


import requests

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

    def fetch(self, pk):
        """
        Fetches story information.

        Args:
            pk: Primary key of the story.

        Returns:
            Story: A new `Story` object.

        Raises:
            InvalidStoryError: If a valid story is not found.
            StoryPermissionError: If access to the story is denied.
            StorySourceError: If source does not return any data.
        """
        raise NotImplementedError()

    def fetch_data(self, pk):
        """
        Fetches story content data.

        Args:
            pk: Primary key of the story.

        Returns:
            bytes: Story content data.

        Raises:
            InvalidStoryError: If a valid story is not found.
            StoryPermissionError: If access to the story is denied.
            StorySourceError: If source does not return any data.
        """
        raise NotImplementedError()

    def fetch_meta(self, pk):
        """
        Fetches story meta information.

        Args:
            pk: Primary key of the story.

        Returns:
            dict: Story meta information.

        Raises:
            InvalidStoryError: If a valid story is not found.
            StoryPermissionError: If access to the story is denied.
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

    def fetch_data(self, pk):
        response = self.get(self.data_path, story=pk, html=True)
        data = response.content

        if len(data) == 0:
            raise InvalidStoryError("Server returned empty response body.")

        if b'<a name=\'1\'></a><h3>' not in data:
            raise InvalidStoryError("Server did not return any chapters.")

        if not data.endswith(b'</html>'):
            raise StorySourceError("Server returned incomplete response.")

        return data

    def fetch_meta(self, pk):
        response = self.get(self.meta_path, story=pk)

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
