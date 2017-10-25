"""
Selectors for Fimfarchive.
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


from fimfarchive.exceptions import InvalidStoryError
from fimfarchive.flavors import UpdateStatus
from fimfarchive.mappers import StoryDateMapper


__all__ = (
    'Selector',
    'RefetchSelector',
    'UpdateSelector',
)


class Selector:
    """
    Picks one of the two supplied stories.
    """

    def __call__(self, old, new):
        """
        Returns either the old or the new story.

        Args:
            old: The currently available story.
            new: The potential replacement story.

        Returns:
            Story: One of the two story objects.
        """
        raise NotImplementedError()


class UpdateSelector(Selector):
    """
    Selects the new story if it needs to be updated.

    An `UpdateStatus` flavor is applied to all returned stories. The
    returned story will also be fully fetched. The selector will not
    attempt to fetch data from new stories unless they have changed.
    """

    def __init__(self, date_mapper=None):
        """
        Constructor.

        Args:
            date_mapper: Maps a `Story` to its modification date.
        """
        if date_mapper:
            self.date_mapper = date_mapper
        else:
            self.date_mapper = StoryDateMapper()

    def filter_empty(self, story):
        """
        Returns the story if it has chapters, otherwise None.
        """
        meta = getattr(story, 'meta', None)

        if meta and meta.get('chapters'):
            return story
        else:
            return None

    def filter_invalid(self, story):
        """
        Returns the story if it is valid, otherwise None.
        """
        try:
            story.meta
            story.data
        except InvalidStoryError:
            return None
        else:
            return story

    def filter_unchanged(self, old, new):
        """
        Returns the new story if it has changed, otherwise None.

        Raises:
            ValueError: If `date_mapper` returns `None`.
        """
        old_date = self.date_mapper(old)
        new_date = self.date_mapper(new)

        if old_date is None:
            raise ValueError("Missing old date.")
        elif new_date is None:
            raise ValueError("Missing new date.")
        elif old_date < new_date:
            return new
        else:
            return None

    def flavored(self, story, *flavors):
        """
        Returns the story after applying the specified flavors.
        """
        story.flavors.update(flavors)

        return story

    def __call__(self, old, new):
        old = self.filter_empty(old)
        new = self.filter_empty(new)
        deleted = old and not new

        if old:
            old = self.filter_invalid(old)

        if old and new:
            new = self.filter_unchanged(old, new)

        if new:
            new = self.filter_invalid(new)
            deleted = old and not new

        if not old and new:
            return self.flavored(new, UpdateStatus.CREATED)
        elif old and not new and not deleted:
            return self.flavored(old, UpdateStatus.REVIVED)
        elif old and new:
            return self.flavored(new, UpdateStatus.UPDATED)
        elif old and not new and deleted:
            return self.flavored(old, UpdateStatus.DELETED)
        else:
            return None


class RefetchSelector(UpdateSelector):
    """
    Selects the new story if it is available.
    """

    def filter_unchanged(self, old, new):
        """
        Returns the new story.
        """
        return new
