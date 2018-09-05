"""
Fimfiction APIv2 fetcher tests.
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


import json
import os

import pytest

from fimfarchive.exceptions import InvalidStoryError
from fimfarchive.fetchers import Fimfiction2Fetcher
from fimfarchive.utils import JayWalker

from tests.fixtures.responses import Recorder


VALID_STORY_KEY = 9
AVATAR_STORY_KEY = 5764
COVER_STORY_KEY = 444
PUBLISHED_STORY_KEY = 25739

INVALID_STORY_KEY = 7
EMPTY_STORY_KEY = 199462
HIDDEN_STORY_KEY = 8
PROTECTED_STORY_KEY = 208799

AVATAR_PLACEHOLDER = {
    '32': 'https://static.fimfiction.net/images/none_32.png',
    '64': 'https://static.fimfiction.net/images/none_64.png',
}

BULK_COMBINATIONS = [
    (False, False),
    (False, True),
    (True, False),
    (True, True),
]


class Redactor(JayWalker):
    """
    Redacts recorded responses.
    """

    def handle(self, data, key, value) -> None:
        key = str(key)

        if key.endswith('_html') or key == 'short_description':
            data[key] = "REDACTED"
        else:
            self.walk(value)


class TestFimfiction2Fetcher:
    """
    Fimfarchive2Fetcher tests.
    """

    @pytest.fixture(params=BULK_COMBINATIONS)
    def fetcher(self, responses, request):
        """
        Returns a Fimfarchive2Fetcher instance.
        """
        bulk_meta, bulk_data = request.param
        token = os.environ.get('FIMFICTION_ACCESS_TOKEN', 'None')
        fetcher = Fimfiction2Fetcher(token, bulk_meta, bulk_data)

        fetcher.requester.bulk.bulk_size = 2
        fetcher.prefetch_meta = False
        fetcher.prefetch_data = False

        if isinstance(responses, Recorder):
            responses.walker = Redactor()

        yield fetcher

    def fetch_valid(self, fetcher, key):
        """
        Fetches a valid story.
        """
        story = fetcher.fetch(key)

        assert story.meta['id'] == key
        assert json.loads(story.data.decode())

        return story

    def fetch_invalid(self, fetcher, key):
        """
        Fetches an invalid story.
        """
        story = fetcher.fetch(key)

        with pytest.raises(InvalidStoryError):
            story.meta

        with pytest.raises(InvalidStoryError):
            story.data

        return story

    def test_valid(self, fetcher):
        """
        Tests fetching a valid story.
        """
        self.fetch_valid(fetcher, VALID_STORY_KEY)

    def test_valid_missing_cover(self, fetcher):
        """
        Tests fetching a valid story without cover.
        """
        story = self.fetch_valid(fetcher, COVER_STORY_KEY)
        assert story.meta['cover_image'] is None

    def test_valid_missing_avatar(self, fetcher):
        """
        Tests fetching a valid story without avatar.
        """
        story = self.fetch_valid(fetcher, AVATAR_STORY_KEY)
        avatar = story.meta['author']['avatar']

        assert AVATAR_PLACEHOLDER['32'] == avatar['32']
        assert AVATAR_PLACEHOLDER['64'] == avatar['64']
        assert AVATAR_PLACEHOLDER['64'] == avatar['96']

    def test_valid_missing_published_date(self, fetcher):
        """
        Tests fetching a valid story without published date.
        """
        story = self.fetch_valid(fetcher, PUBLISHED_STORY_KEY)
        assert story.meta['date_published'] is None

    def test_empty_story(self, fetcher):
        """
        Test fetching a story without chapters.
        """
        story = fetcher.fetch(EMPTY_STORY_KEY)
        assert story.meta['id'] == EMPTY_STORY_KEY

        with pytest.raises(InvalidStoryError):
            story.data

    def test_invalid_story(self, fetcher):
        """
        Tests fetching an invalid story.
        """
        self.fetch_invalid(fetcher, INVALID_STORY_KEY)

    def test_hidden_story(self, fetcher):
        """
        Tests fetching a hidden story.
        """
        self.fetch_invalid(fetcher, HIDDEN_STORY_KEY)

    def test_protected_story(self, fetcher):
        """
        Tests fetching a password-protected story.
        """
        self.fetch_invalid(fetcher, PROTECTED_STORY_KEY)
