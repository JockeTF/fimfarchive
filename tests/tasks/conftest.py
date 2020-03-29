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


from copy import deepcopy
from typing import Dict

from fimfarchive.exceptions import InvalidStoryError
from fimfarchive.converters import Converter
from fimfarchive.fetchers import Fetcher
from fimfarchive.stories import Story
from fimfarchive.utils import Empty


class DummyConverer(Converter):
    """
    Converter that increments a counter.
    """

    def __call__(self, story: Story) -> Story:
        meta = deepcopy(story.meta)
        meta['conversions'] += 1

        return story.merge(meta=meta)


class DummyFetcher(Fetcher):
    """
    Fetcher with local instance storage.
    """

    def __init__(self):
        """
        Constructor.
        """
        self.stories: Dict[int, Story] = dict()

    def add(self, key, date, flavors=(), data=Empty):
        """
        Adds a story to the fetcher.
        """
        meta = {
            'id': key,
            'title': f't{key}',
            'date_modified': date,
            'conversions': 0,
            'author': {
                'id': key,
                'name': f'n{key}'
            },
            'chapters': [
                {'id': key},
            ],
        }

        if data is Empty:
            text = f'd{key}'
            data = text.encode()

        story = Story(
            key=key,
            fetcher=self,
            meta=meta,
            data=data,
            flavors=flavors,
        )

        self.stories[key] = story

        return story

    def fetch(self, key, prefetch_meta=None, prefetch_data=None):
        """
        Returns a previously stored story.
        """
        try:
            return self.stories[key]
        except KeyError:
            raise InvalidStoryError()

    def fetch_data(self, key):
        """
        Raises exception for missing data.
        """
        raise InvalidStoryError()

    def fetch_meta(self, key):
        """
        Raises exception for missing meta.
        """
        raise InvalidStoryError()

    def __iter__(self):
        """
        Yields all previously stored stories.
        """
        for key in sorted(self.stories.keys()):
            yield self.stories[key]
