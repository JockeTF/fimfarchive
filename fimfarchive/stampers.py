"""
Stampers for Fimfarchive.
"""


#
# Fimfarchive, preserves stories from Fimfiction.
# Copyright (C) 2019  Joakim Soderlund
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


from typing import Any, Callable, Dict, Optional, Set

import arrow

from fimfarchive.flavors import Flavor, UpdateStatus
from fimfarchive.stories import Story
from fimfarchive.utils import find_flavor


__all__ = (
    'Stamper',
    'UpdateStamper',
)


class Stamper:
    """
    Adds archive-related information to stories.
    """

    def get_archive(self, story: Story) -> Dict[str, Any]:
        """
        Finds or creates an archive dict.

        Args:
            story: The story to stamp.

        Returns:
            An archive dict for the story.
        """
        meta = story.meta

        if 'archive' not in meta:
            meta['archive'] = dict()

        return meta['archive']

    def __call__(self, story: Story) -> None:
        """
        Applies the stamp to the story.

        Args:
            story: The story to stamp.
        """
        raise NotImplementedError()


class UpdateStamper(Stamper):
    """
    Adds modification dates to stories.
    """
    spec: Dict[str, Set[UpdateStatus]] = {
        'date_created': {
            UpdateStatus.CREATED,
        },
        'date_fetched': {
            UpdateStatus.CREATED,
            UpdateStatus.REVIVED,
            UpdateStatus.UPDATED,
        },
        'date_updated': {
            UpdateStatus.CREATED,
            UpdateStatus.UPDATED,
        },
    }

    def __call__(self, story: Story) -> None:
        """
        Applies modification dates to a story.

        Args:
            story: The story to stamp.
        """
        timestamp = arrow.utcnow().isoformat()
        flavor = find_flavor(story, UpdateStatus)
        archive = self.get_archive(story)

        archive['date_checked'] = timestamp

        for key, value in self.spec.items():
            if flavor in value:
                archive[key] = timestamp
            elif key not in archive:
                archive[key] = None


class FlavorStamper(Stamper):
    """
    Adds flavors to stories.
    """

    def __init__(self, mapper: Callable[[Story], Optional[Flavor]]) -> None:
        """
        Constructor.

        Args:
            mapper: Callable returning the flavor to stamp with.
        """
        self.map = mapper

    def __call__(self, story: Story) -> None:
        flavor = self.map(story)

        if flavor:
            story.flavors.add(flavor)


class PathStamper(Stamper):
    """
    Adds archive paths to stories.
    """

    def __init__(self, mapper: Callable[[Story], Optional[str]]) -> None:
        """
        Constructor.

        Args:
            mapper: Callable returning the path to stamp with.
        """
        self.map = mapper

    def __call__(self, story: Story) -> None:
        archive = self.get_archive(story)
        path = self.map(story)

        if 'path' in archive:
            del archive['path']

        if 'path' in story.meta:
            del story.meta['path']

        if path:
            archive['path'] = path
