"""
Fimfarchive fetcher tests.
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


import pytest

from fimfarchive.exceptions import InvalidStoryError, StorySourceError
from fimfarchive.fetchers import FimfarchiveFetcher


VALID_STORY_KEY = 9
INVALID_STORY_KEY = 7

FIMFARCHIVE_PATH = 'fimfarchive.zip'


class TestFimfarchiveFetcher:
    """
    FimfarchiveFetcher tests.
    """

    @pytest.fixture(scope='module')
    def fetcher(self):
        """
        Returns the fetcher instance to test.
        """
        with FimfarchiveFetcher(FIMFARCHIVE_PATH) as fetcher:
            yield fetcher

    def test_closed_fetcher_raises_exception(self):
        """
        Tests `StorySourceError` is raised when fetcher is closed.
        """
        with FimfarchiveFetcher(FIMFARCHIVE_PATH) as fetcher:
            fetcher.fetch_meta(VALID_STORY_KEY)

        with pytest.raises(StorySourceError):
            fetcher.fetch_meta(VALID_STORY_KEY)

    def test_fetch_meta_for_valid_story(self, fetcher):
        """
        Tests meta is returned if story is valid
        """
        meta = fetcher.fetch_meta(VALID_STORY_KEY)
        assert meta['id'] == VALID_STORY_KEY

    def test_fetch_meta_for_invalid_story(self, fetcher):
        """
        Tests `InvalidStoryError` is raised if story is invalid.
        """
        with pytest.raises(InvalidStoryError):
            fetcher.fetch_meta(INVALID_STORY_KEY)

    def test_fetch_data_for_valid_story(self, fetcher):
        """
        Tests data is returned if story is valid.
        """
        data = fetcher.fetch_data(VALID_STORY_KEY)
        assert len(data) != 0

    def test_fetch_data_for_invalid_story(self, fetcher):
        """
        Tests `InvalidStoryError` is raised if story is invalid.
        """
        with pytest.raises(InvalidStoryError):
            fetcher.fetch_data(INVALID_STORY_KEY)

    @pytest.mark.parametrize('attr', ('archive', 'index', 'paths'))
    def test_close_when_missing_attribute(self, attr):
        """
        Tests close works even after partial initialization.
        """
        with FimfarchiveFetcher(FIMFARCHIVE_PATH) as fetcher:
            delattr(fetcher, attr)
