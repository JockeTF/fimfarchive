"""
Fimfiction fetcher.
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
from fimfarchive.flavors import StorySource, DataFormat, MetaFormat, MetaPurity

from .base import Fetcher


__all__ = (
    'FimfictionFetcher',
)


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
        MetaFormat.ALPHA,
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
