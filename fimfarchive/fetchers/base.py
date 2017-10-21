"""
Base fetcher.
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


from typing import FrozenSet

from fimfarchive.flavors import Flavor
from fimfarchive.stories import Story


__all__ = (
    'Fetcher',
)


class Fetcher:
    """
    Abstract base class for story fetchers.
    """
    prefetch_meta = False
    prefetch_data = False

    flavors: FrozenSet[Flavor] = frozenset()

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
