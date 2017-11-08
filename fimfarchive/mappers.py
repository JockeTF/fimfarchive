"""
Mappers for Fimfarchive.
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


import os
from abc import abstractmethod
from typing import Generic, Optional, TypeVar

from arrow import api as arrow, Arrow

from fimfarchive.exceptions import InvalidStoryError
from fimfarchive.stories import Story


__all__ = (
    'Mapper',
    'StaticMapper',
    'StoryDateMapper',
    'StoryPathMapper',
)


T = TypeVar('T')


class Mapper(Generic[T]):
    """
    Callable which maps stories to something else.
    """

    @abstractmethod
    def __call__(self, story: Story) -> T:
        """
        Applies the mapper.

        Args:
            story: The story to map.

        Returns:
            A mapped object.
        """


class StaticMapper(Mapper[T]):
    """
    Returns the supplied value for any call.
    """

    def __init__(self, value: T) -> None:
        self.value = value

    def __call__(self, story: Story) -> T:
        return self.value


class StoryDateMapper(Mapper[Optional[Arrow]]):
    """
    Returns the latest timestamp in a story, or None.
    """

    def __call__(self, story: Story) -> Optional[Arrow]:
        try:
            meta = getattr(story, 'meta', None)
        except InvalidStoryError:
            return None

        if not meta:
            return None

        dates = {
            meta.get('date_modified'),
        }

        for chapter in meta.get('chapters') or tuple():
            dates.add(chapter.get('date_modified'))

        dates.discard(None)

        if dates:
            return max(arrow.get(date) for date in dates)
        else:
            return None


class StoryPathMapper(Mapper[str]):
    """
    Returns a key-based file path for a story.
    """

    def __init__(self, directory: str) -> None:
        self.directory = directory

    def __call__(self, story: Story) -> str:
        directory = str(self.directory)
        key = str(story.key)

        return os.path.join(directory, key)
