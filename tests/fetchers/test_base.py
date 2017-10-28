"""
Base fetcher tests.
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


VALID_STORY_KEY = 9


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
