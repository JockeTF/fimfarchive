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
