"""
Fetcher tests.
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
from fimfarchive.fetchers import FimfarchiveFetcher, FimfictionFetcher


VALID_STORY_KEY = 9
INVALID_STORY_KEY = 7
EMPTY_STORY_KEY = 8
PROTECTED_STORY_KEY = 208799

FIMFARCHIVE_PATH = 'fimfarchive-20160525.zip'


class TestFimfictionFetcher:
    """
    FimfictionFetcher tests.
    """
    fetcher = None

    @classmethod
    def setup_class(cls):
        cls.fetcher = FimfictionFetcher()

    @classmethod
    def teardown_class(cls):
        cls.fetcher = None

    def test_with_statment(self):
        """
        Tests fetcher can be used in with statements.
        """
        with FimfictionFetcher() as fetcher:
            fetcher.get('http://example.com/')

    def test_get_for_invalid_host(self):
        """
        Tests `StorySourceError` is raised if server is unreachable.
        """
        with pytest.raises(StorySourceError):
            self.fetcher.get('http://-')

    def test_get_for_invalid_page(self):
        """
        Tests `StorySourceError` is raised if page does not exist.

        Since Fimfiction always returns HTTP 200 OK, even for invalid stories,
        other HTTP status codes indicate that something else has gone wrong.
        """
        with pytest.raises(StorySourceError):
            self.fetcher.get('http://example.com/-')

    def test_fetch_meta_for_valid_story(self):
        """
        Tests meta is returned if story is valid
        """
        meta = self.fetcher.fetch_meta(VALID_STORY_KEY)
        assert meta['id'] == VALID_STORY_KEY
        assert meta['words'] != 0

    def test_fetch_meta_for_invalid_story(self):
        """
        Tests `InvalidStoryError` is raised if story is invalid.
        """
        with pytest.raises(InvalidStoryError):
            self.fetcher.fetch_meta(INVALID_STORY_KEY)

    def test_fetch_meta_for_empty_story(self):
        """
        Tests meta is returned if story is empty.

        It would be feasible for the fetcher to raise `InvalidStoryError` here
        since the story data is useless. But because the meta of such stories
        may still be of interest, it was decided that meta should be returned.
        """
        meta = self.fetcher.fetch_meta(EMPTY_STORY_KEY)
        assert meta['id'] == EMPTY_STORY_KEY
        assert meta['words'] == 0

    def test_fetch_meta_for_protected_story(self):
        """
        Tests meta is returned if story is protected.

        It would be feasible for the fetcher to raise `InvalidStoryError` here
        since the story data is inaccessible. However, there is no way to
        determine that a story is password-protected from its meta data.
        """
        meta = self.fetcher.fetch_meta(PROTECTED_STORY_KEY)
        assert meta['id'] == PROTECTED_STORY_KEY
        assert meta['words'] != 0

    def test_fetch_data_for_valid_story(self):
        """
        Tests data is returned if story is valid.
        """
        data = self.fetcher.fetch_data(VALID_STORY_KEY)
        assert len(data) != 0

    def test_fetch_data_for_invalid_story(self):
        """
        Tests `InvalidStoryError` is raised if story is invalid.
        """
        with pytest.raises(InvalidStoryError):
            self.fetcher.fetch_data(INVALID_STORY_KEY)

    def test_fetch_data_for_empty_story(self):
        """
        Tests `InvalidStoryError` is raised if story is empty.
        """
        with pytest.raises(InvalidStoryError):
            self.fetcher.fetch_data(EMPTY_STORY_KEY)

    def test_fetch_data_for_protected_story(self):
        """
        Tests `InvalidStoryError` is raised if story is protected.
        """
        with pytest.raises(InvalidStoryError):
            self.fetcher.fetch_data(PROTECTED_STORY_KEY)


class TestFimfarchiveFetcher:
    """
    FimfarchiveFetcher tests.
    """
    fetcher = None

    @classmethod
    def setup_class(cls):
        cls.fetcher = FimfarchiveFetcher(FIMFARCHIVE_PATH)

    @classmethod
    def teardown_class(cls):
        cls.fetcher.close()
        cls.fetcher = None

    def test_with_statment(self):
        """
        Tests fetcher can be used in with statements.
        """
        with FimfarchiveFetcher(FIMFARCHIVE_PATH) as fetcher:
            fetcher.lookup(VALID_STORY_KEY)

        with pytest.raises(StorySourceError):
            fetcher.lookup(VALID_STORY_KEY)

    def test_fetch_meta_for_valid_story(self):
        """
        Tests meta is returned if story is valid
        """
        meta = self.fetcher.fetch_meta(VALID_STORY_KEY)
        assert meta['id'] == VALID_STORY_KEY
        assert meta['words'] != 0

    def test_fetch_meta_for_invalid_story(self):
        """
        Tests `InvalidStoryError` is raised if story is invalid.
        """
        with pytest.raises(InvalidStoryError):
            self.fetcher.fetch_meta(INVALID_STORY_KEY)

    def test_fetch_data_for_valid_story(self):
        """
        Tests data is returned if story is valid.
        """
        data = self.fetcher.fetch_data(VALID_STORY_KEY)
        assert len(data) != 0

    def test_fetch_data_for_invalid_story(self):
        """
        Tests `InvalidStoryError` is raised if story is invalid.
        """
        with pytest.raises(InvalidStoryError):
            self.fetcher.fetch_data(INVALID_STORY_KEY)
