"""
Stories for Fimfarchive.
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


__all__ = (
    'Story',
)


class Story:
    """
    Represents a story.
    """

    def __init__(self, key, fetcher=None, meta=None, data=None, flavors=()):
        if fetcher is None and (data is None or meta is None):
            raise ValueError("Story must contain fetcher if lazy.")

        self.key = key
        self.fetcher = fetcher
        self.flavors = set(flavors)
        self._meta = meta
        self._data = data

    @property
    def is_fetched(self):
        """
        True if no more fetches are necessary.
        """
        return self.has_meta and self.has_data

    @property
    def has_meta(self):
        """
        True if story meta has been fetched.
        """
        return self._meta is not None

    @property
    def meta(self):
        """
        Returns the story meta.

        Meta may be fetched if this story instance is lazy.

        Raises:
            InvalidStoryError: If a valid story is not found.
            StorySourceError: If source does not return any data.
        """
        if not self.has_meta:
            self._meta = self.fetcher.fetch_meta(self.key)

        return self._meta

    @property
    def has_data(self):
        """
        True if story data has been fetched.
        """
        return self._data is not None

    @property
    def data(self):
        """
        Returns the story data.

        Data may be fetched if this story instance is lazy.

        Raises:
            InvalidStoryError: If a valid story is not found.
            StorySourceError: If source does not return any data.
        """
        if not self.has_data:
            self._data = self.fetcher.fetch_data(self.key)

        return self._data

    def merge(self, **params):
        """
        Returns a shallow copy, optionally replacing attributes.

        Args:
            **params: Overrides parameters from the current instance.

        Raises:
            TypeError: If passed an unexpected parameter.
        """
        kwargs = {k.lstrip('_'): v for k, v in vars(self).items()}
        kwargs.update(params)

        return type(self)(**kwargs)
