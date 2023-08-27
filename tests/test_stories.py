"""
Story tests.
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

from fimfarchive.stories import Story
from fimfarchive.exceptions import FimfarchiveError


KEY = 1


class TestStory:
    """
    Story tests.
    """

    @pytest.fixture
    def meta(self):
        """
        Returns some fake story meta.
        """
        return {'id': KEY}

    @pytest.fixture
    def data(self):
        """
        Returns some fake story data.
        """
        return b'<html />'

    def test_init(self, fetcher, meta, data):
        """
        Tests story initialization.
        """
        story = Story(KEY, fetcher, meta, data)

        assert story.key == KEY
        assert story.fetcher == fetcher
        assert story.has_meta and story.meta == meta
        assert story.has_data and story.data == data

    def test_init_with_fetcher_only(self, fetcher):
        """
        Tests lazy story can be initialized.
        """
        story = Story(KEY, fetcher)

        assert story.key == KEY
        assert story.fetcher == fetcher

    def test_init_with_meta_and_data_only(self, meta, data):
        """
        Test story can be initialized with only meta and data.
        """
        story = Story(KEY, None, meta, data)

        assert story.key == KEY
        assert story.has_data and story.data == data
        assert story.has_meta and story.meta == meta

    def test_init_without_fetcher_nor_meta(self, data):
        """
        Tests `ValueError` is raised on init without fetcher nor meta.
        """
        with pytest.raises(ValueError):
            Story(KEY, None, None, data)

    def test_init_without_fetcher_nor_data(self, meta):
        """
        Tests `ValueError` is raised on init without fetcher nor data.
        """
        with pytest.raises(ValueError):
            Story(KEY, None, meta, None)

    def test_init_without_fetcher_nor_both(self):
        """
        Tests `ValueError` is raised on init without fetcher, meta, nor data.
        """
        with pytest.raises(ValueError):
            Story(KEY, None)

    def test_fetch_meta_from_fetcher(self, fetcher, meta, data):
        """
        Tests lazy story fetches meta once from fetcher.
        """
        fetcher.fetch_meta.return_value = meta
        story = Story(KEY, fetcher, None, data)

        assert not story.has_meta
        fetcher.fetch_meta.assert_not_called()
        assert story.meta == meta
        assert story.has_meta
        assert story.meta == meta
        fetcher.fetch_meta.assert_called_once_with(KEY)

    def test_fetch_data_from_fetcher(self, fetcher, meta, data):
        """
        Tests lazy story fetches data once from fetcher.
        """
        fetcher.fetch_data.return_value = data
        story = Story(KEY, fetcher, meta, None)

        assert not story.has_data
        fetcher.fetch_data.assert_not_called()
        assert story.data == data
        assert story.has_data
        assert story.data == data
        fetcher.fetch_data.assert_called_once_with(KEY)

    def test_meta_not_fetched_unless_necessary(self, fetcher, meta):
        """
        Test `fetch_meta` not called unless necessary.
        """
        story = Story(KEY, fetcher, meta, None)

        assert story.has_meta and story.meta == meta
        fetcher.fetch_meta.assert_not_called()

    def test_data_not_fetched_unless_necessary(self, fetcher, data):
        """
        Test `fetch_data` not called unless necessary.
        """
        story = Story(KEY, fetcher, None, data)

        assert story.has_data and story.data == data
        fetcher.fetch_data.assert_not_called()

    def test_is_fetched(self, fetcher, meta, data):
        """
        Tests `is_fetched` requires both meta and data.
        """
        fetcher.fetch_meta.return_value = meta
        fetcher.fetch_data.return_value = data
        story = Story(KEY, fetcher)

        assert not story.is_fetched
        assert story.meta == meta
        assert not story.is_fetched
        assert story.data == data
        assert story.is_fetched

    def test_raises_fetch_meta_exception(self, fetcher):
        """
        Tests exception from meta fetch is raised.
        """
        fetcher.fetch_meta.side_effect = FimfarchiveError()
        story = Story(KEY, fetcher)

        assert not story.has_meta

        with pytest.raises(FimfarchiveError):
            story.meta

        assert not story.has_meta

    def test_raises_fetch_data_exception(self, fetcher):
        """
        Tests exception from data fetch is raised.
        """
        fetcher.fetch_data.side_effect = FimfarchiveError()
        story = Story(KEY, fetcher)

        assert not story.has_data

        with pytest.raises(FimfarchiveError):
            story.data

        assert not story.has_data

    def test_flavors_are_copied(self, fetcher, flavor):
        """
        Tests story flavor change does not affect fetcher.
        """
        flavors = {flavor.A}
        story = Story(KEY, fetcher, flavors=flavors)
        story.flavors.remove(flavor.A)

        assert story.flavors is not flavors
        assert story.flavors == set()
        assert flavors == {flavor.A}

    def test_flavors_are_stored_in_set(self, fetcher, flavor):
        """
        Tests flavor sequence is converted to set.
        """
        flavors = [flavor.A]
        story = Story(KEY, fetcher, flavors=flavors)

        assert story.flavors is not flavors
        assert story.flavors == {flavor.A}
        assert type(story.flavors) is set

    def test_merge_without_parameters(self, story):
        """
        Tests `merge` returns new story containing current attributes.
        """
        merge = story.merge()

        assert merge is not story
        assert merge.data is story.data
        assert merge.meta is story.meta

        for k, v in vars(story).items():
            assert getattr(merge, k) == v

    def test_merge_with_parameters(self, story):
        """
        Tests `merge` can override attributes.
        """
        meta = dict(story.meta)
        merge = story.merge(meta=meta)

        assert meta is not story.meta
        assert meta is merge.meta

    def test_merge_with_invalid_state(self, story):
        """
        Tests `merge` is affected by validation in `__init__`.
        """
        with pytest.raises(ValueError):
            story.merge(fetcher=None, meta=None)

    def test_merge_with_invalid_arguments(self, story):
        """
        Tests `merge` cannot create story using invalid arguments.
        """
        with pytest.raises(TypeError):
            story.merge(alpaca=True)
