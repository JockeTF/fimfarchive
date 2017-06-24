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


from unittest.mock import MagicMock

import pytest

from fimfarchive.exceptions import InvalidStoryError, StorySourceError
from fimfarchive.fetchers import FimfarchiveFetcher, FimfictionFetcher


VALID_STORY_KEY = 9
INVALID_STORY_KEY = 7
EMPTY_STORY_KEY = 8
PROTECTED_STORY_KEY = 208799

FIMFARCHIVE_PATH = 'fimfarchive-20170601.zip'


class TestFetcher:
    """
    Fetcher tests.
    """

    def test_fetch_with_prefetch_meta(self, fetcher):
        """
        Tests `fetch_meta` is called when prefetch_meta is enabled.
        """
        fetcher.fetch(VALID_STORY_KEY, prefetch_meta=True)
        fetcher.fetch_meta.assert_called_once_with(VALID_STORY_KEY)

    def test_fetch_without_prefetch_meta(self, fetcher):
        """
        Tests `fetch_meta` is not called when prefetch_meta is disabled.
        """
        fetcher.fetch(VALID_STORY_KEY, prefetch_meta=False)
        fetcher.fetch_meta.assert_not_called()

    def test_fetch_with_prefetch_data(self, fetcher):
        """
        Tests `fetch_data` is called when prefetch_data is enabled.
        """
        fetcher.fetch(VALID_STORY_KEY, prefetch_data=True)
        fetcher.fetch_data.assert_called_once_with(VALID_STORY_KEY)

    def test_fetch_without_prefetch_data(self, fetcher):
        """
        Tests `fetch_data` is not called when prefetch_data is disabled.
        """
        fetcher.fetch(VALID_STORY_KEY, prefetch_data=False)
        fetcher.fetch_data.assert_not_called()

    def test_fetch_with_default_prefetch(self, fetcher):
        """
        Tests prefetching can be enabled using attributes.
        """
        fetcher.prefetch_meta = True
        fetcher.prefetch_data = True

        fetcher.fetch(VALID_STORY_KEY)

        fetcher.fetch_meta.assert_called_once_with(VALID_STORY_KEY)
        fetcher.fetch_data.assert_called_once_with(VALID_STORY_KEY)

    def test_fetch_without_default_prefetch(self, fetcher):
        """
        Tests prefetching can be disabled using attributes.
        """
        fetcher.prefetch_meta = False
        fetcher.prefetch_data = False

        fetcher.fetch(VALID_STORY_KEY)

        fetcher.fetch_meta.assert_not_called()
        fetcher.fetch_data.assert_not_called()

    def test_close_is_called_on_exit(self, fetcher):
        """
        Test `close` is called on exit in with statement.
        """
        fetcher.close = MagicMock(method='close')

        with fetcher:
            pass

        fetcher.close.assert_called_once_with()

    def test_empty_flavors_are_passed_to_story(self, fetcher):
        """
        Tests story contains empty flavors from fetcher.
        """
        fetcher.flavors = set()
        story = fetcher.fetch(VALID_STORY_KEY)
        assert story.flavors == set()

    def test_custom_flavors_are_passed_to_story(self, fetcher, flavor):
        """
        Tests story contains custom flavors from fetcher.
        """
        fetcher.flavors = {flavor.A}
        story = fetcher.fetch(VALID_STORY_KEY)
        assert story.flavors == {flavor.A}


class TestFimfictionFetcher:
    """
    FimfictionFetcher tests.
    """

    @pytest.fixture
    def fetcher(self):
        """
        Returns the fetcher instance to test.
        """
        return FimfictionFetcher()

    def test_with_statment(self):
        """
        Tests fetcher can be used in with statements.
        """
        with FimfictionFetcher() as fetcher:
            fetcher.get('http://example.com/')

    def test_get_for_invalid_host(self, fetcher):
        """
        Tests `StorySourceError` is raised if server is unreachable.
        """
        with pytest.raises(StorySourceError):
            fetcher.get('http://-')

    def test_get_for_invalid_page(self, fetcher):
        """
        Tests `StorySourceError` is raised if page does not exist.

        Since Fimfiction always returns HTTP 200 OK, even for invalid stories,
        other HTTP status codes indicate that something else has gone wrong.
        """
        with pytest.raises(StorySourceError):
            fetcher.get('http://example.com/-')

    def test_fetch_meta_for_valid_story(self, fetcher):
        """
        Tests meta is returned if story is valid
        """
        meta = fetcher.fetch_meta(VALID_STORY_KEY)
        assert meta['id'] == VALID_STORY_KEY
        assert meta['words'] != 0

    def test_fetch_meta_for_invalid_story(self, fetcher):
        """
        Tests `InvalidStoryError` is raised if story is invalid.
        """
        with pytest.raises(InvalidStoryError):
            fetcher.fetch_meta(INVALID_STORY_KEY)

    def test_fetch_meta_for_empty_story(self, fetcher):
        """
        Tests meta is returned if story is empty.

        It would be feasible for the fetcher to raise `InvalidStoryError` here
        since the story data is useless. But because the meta of such stories
        may still be of interest, it was decided that meta should be returned.
        """
        meta = fetcher.fetch_meta(EMPTY_STORY_KEY)
        assert meta['id'] == EMPTY_STORY_KEY
        assert meta['words'] == 0

    def test_fetch_meta_for_protected_story(self, fetcher):
        """
        Tests meta is returned if story is protected.

        It would be feasible for the fetcher to raise `InvalidStoryError` here
        since the story data is inaccessible. However, there is no way to
        determine that a story is password-protected from its meta data.
        """
        meta = fetcher.fetch_meta(PROTECTED_STORY_KEY)
        assert meta['id'] == PROTECTED_STORY_KEY
        assert meta['words'] != 0

    def test_fetch_data_for_valid_story(self, fetcher):
        """
        Tests data is returned if story is valid.
        """
        data = fetcher.fetch_data(VALID_STORY_KEY)
        assert len(data) != 0

    @pytest.mark.xfail(reason='knighty/fimfiction-issues#139')
    def test_fetch_data_for_invalid_story(self, fetcher):
        """
        Tests `InvalidStoryError` is raised if story is invalid.
        """
        with pytest.raises(InvalidStoryError):
            fetcher.fetch_data(INVALID_STORY_KEY)

    def test_fetch_data_for_empty_story(self, fetcher):
        """
        Tests `InvalidStoryError` is raised if story is empty.
        """
        with pytest.raises(InvalidStoryError):
            fetcher.fetch_data(EMPTY_STORY_KEY)

    def test_fetch_data_for_protected_story(self, fetcher):
        """
        Tests `InvalidStoryError` is raised if story is protected.
        """
        with pytest.raises(InvalidStoryError):
            fetcher.fetch_data(PROTECTED_STORY_KEY)


class TestFimfarchiveFetcher:
    """
    FimfarchiveFetcher tests.
    """

    @pytest.yield_fixture(scope='module')
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
            fetcher.lookup(VALID_STORY_KEY)

        with pytest.raises(StorySourceError):
            fetcher.lookup(VALID_STORY_KEY)

    def test_fetch_meta_for_valid_story(self, fetcher):
        """
        Tests meta is returned if story is valid
        """
        meta = fetcher.fetch_meta(VALID_STORY_KEY)
        assert meta['id'] == VALID_STORY_KEY
        assert meta['words'] != 0

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
