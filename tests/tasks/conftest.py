"""
Common task fixtures.
"""


#
# Fimfarchive, preserves stories from Fimfiction.
# Copyright (C) 2020  Joakim Soderlund
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


from typing import Dict

import pytest

from fimfarchive.exceptions import InvalidStoryError
from fimfarchive.fetchers import Fetcher
from fimfarchive.stories import Story


class DummyFetcher(Fetcher):
    """
    Fetcher with local instance storage.
    """

    def __init__(self):
        """
        Constructor.
        """
        self.stories: Dict[int, Story] = dict()

    def add(self, key, date, flavors=()):
        """
        Adds a story to the fetcher.
        """
        story = Story(
            key=key,
            flavors=flavors,
            data=f'Story {key}'.encode(),
            meta={
                'id': key,
                'date_modified': date,
                'chapters': [
                    {'id': key},
                ],
            },
        )

        self.stories[key] = story

        return story

    def fetch(self, key):
        """
        Returns a previously stored story.
        """
        try:
            return self.stories[key]
        except KeyError:
            raise InvalidStoryError()


@pytest.fixture
def dummy() -> DummyFetcher:
    """
    Returns a `Fetcher` dummy.
    """
    return DummyFetcher()
