"""
Selector tests.
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


from unittest.mock import patch, Mock, PropertyMock

import pytest

from fimfarchive.exceptions import InvalidStoryError
from fimfarchive.fetchers import Fetcher
from fimfarchive.flavors import UpdateStatus
from fimfarchive.mappers import StoryDateMapper
from fimfarchive.selectors import RefetchSelector, UpdateSelector
from fimfarchive.stories import Story


class TestUpdateSelector:
    """
    UpdateSelector tests.
    """

    @pytest.fixture
    def selector(self):
        """
        Returns a new update selector.
        """
        return UpdateSelector()

    def populate(self, story, date=0):
        """
        Returns a cloned story populated with chapter meta.
        """
        meta = {
            **story.meta,
            'date_modified': date,
            'chapters': [
                {'id': 1},
                {'id': 2},
                {'id': 3},
            ],
        }

        return story.merge(meta=meta)

    def test_filter_empty_with_chapters(self, selector, story):
        """
        Tests `filter_empty` keeps stories containing chapter meta.
        """
        story = self.populate(story, 1)
        selected = selector.filter_empty(story)

        assert selected is story

    def test_filter_empty_without_chapters(self, selector, story):
        """
        Tests `filter_empty` drops stories without chapter meta.
        """
        selected = selector.filter_empty(story)

        assert selected is None

    def test_filter_empty_with_empty_chapters(self, selector, story):
        """
        Tests `filter_empty` drops stories with empty chapter meta.
        """
        meta = {
            **story.meta,
            'chapters': []
        }

        story = story.merge(meta=meta)
        selected = selector.filter_empty(story)

        assert selected is None

    def test_filter_invalid_for_valid(self, selector, story):
        """
        Tests `filter_invalid` keeps valid stories.
        """
        selected = selector.filter_invalid(story)

        assert selected is story

    def test_filter_invalid_without_meta(self, selector, story):
        """
        Tests `filter_invalid` drops stories raising invalid on meta.
        """
        with patch.object(Story, 'meta', new_callable=PropertyMock) as m:
            m.side_effect = InvalidStoryError
            selected = selector.filter_invalid(story)

        assert selected is None

    def test_filter_invalid_without_data(self, selector, story):
        """
        Tests `filter_invalid` drops stories raising invalid on data.
        """
        with patch.object(Story, 'data', new_callable=PropertyMock) as m:
            m.side_effect = InvalidStoryError
            selected = selector.filter_invalid(story)

        assert selected is None

    def test_filter_unchanged_for_changed(self, selector, story):
        """
        Tests `filter_unchanged` keeps changed stories.
        """
        old = self.populate(story, 0)
        new = self.populate(story, 1)

        selected = selector.filter_unchanged(old, new)

        assert selected is new

    def test_filter_unchanged_for_unchanged(self, selector, story):
        """
        Tests `filter_unchanged` drops unchanged stories.
        """
        old = self.populate(story, 0)
        new = self.populate(story, 0)

        selected = selector.filter_unchanged(old, new)

        assert selected is None

    def test_filter_unchanged_default_mapper(self):
        """
        Tests `date_mapper` defaults to `StoryDateMapper`.
        """
        selector = UpdateSelector()

        assert isinstance(selector.date_mapper, StoryDateMapper)

    def test_filter_unchanged_custom_mapper(self, story):
        """
        Tests `date_mapper` can be customised.
        """
        old = self.populate(story, 1)
        new = self.populate(story, 0)

        data = {
            old: 0,
            new: 1,
        }

        date_mapper = data.get
        selector = UpdateSelector(date_mapper=date_mapper)
        selected = selector.filter_unchanged(old, new)

        assert selector.date_mapper is date_mapper
        assert selected is new

    def test_filter_unchanged_missing_old_date(self, selector, story):
        """
        Tests `filter_unchanged` raises `ValueError` on missing old date.
        """
        old = self.populate(story, None)
        new = self.populate(story, 1)

        with pytest.raises(ValueError):
            selector.filter_unchanged(old, new)

    def test_filter_unchanged_missing_new_date(self, selector, story):
        """
        Tests `filter_unchanged` raises `ValueError` on missing new date.
        """
        old = self.populate(story, 1)
        new = self.populate(story, None)

        with pytest.raises(ValueError):
            selector.filter_unchanged(old, new)

    def test_flavored(self, selector, story):
        """
        Tests `flavored` adds specified flavor and returns the story.
        """
        assert UpdateStatus.CREATED not in story.flavors

        flavored = selector.flavored(story, UpdateStatus.CREATED)

        assert story is flavored
        assert UpdateStatus.CREATED in story.flavors

    def test_created_selection(self, selector, story):
        """
        Tests behavior for newly created stories.
        """
        old = None
        new = self.populate(story, 1)

        selected = selector(old, new)

        assert selected is new
        assert UpdateStatus.CREATED in new.flavors

    def test_revived_selection(self, selector, story):
        """
        Tests behavior for stories that have not updated.
        """
        old = self.populate(story, 1)
        new = self.populate(story, 1)

        selected = selector(old, new)

        assert selected is old
        assert UpdateStatus.REVIVED in old.flavors

    def test_updated_selection(self, selector, story):
        """
        Tests behavior for stories that have updated.
        """
        old = self.populate(story, 0)
        new = self.populate(story, 1)

        selected = selector(old, new)

        assert selected is new
        assert UpdateStatus.UPDATED in new.flavors

    def test_deleted_selection(self, selector, story):
        """
        Tests behavior for stories that have been deleted.
        """
        old = self.populate(story, 1)
        new = None

        selected = selector(old, new)

        assert selected is old
        assert UpdateStatus.DELETED in old.flavors

    def test_old_protected_selection(self, selector, story):
        """
        Tests behavior for stories that have become password-protected.
        """
        old = self.populate(story, 0)
        new = self.populate(story, 1)

        fetcher = Mock(spec=Fetcher)
        fetcher.fetch_data.side_effect = InvalidStoryError
        new = new.merge(fetcher=fetcher, data=None)

        selected = selector(old, new)

        fetcher.fetch_data.assert_called_once_with(new.key)
        assert selected is old
        assert UpdateStatus.DELETED in old.flavors

    def test_new_protected_selection(self, selector, story):
        """
        Tests behavior for new password-protected stories.
        """
        new = self.populate(story, 1)

        fetcher = Mock(spec=Fetcher)
        fetcher.fetch_data.side_effect = InvalidStoryError
        new = new.merge(fetcher=fetcher, data=None)

        selected = selector(None, new)

        fetcher.fetch_data.assert_called_once_with(new.key)
        assert selected is None

    def test_invalid_selection(self, selector):
        """
        Tests behavior for invalid stories.
        """
        selected = selector(None, None)

        assert selected is None


class TestRefetchSelector(TestUpdateSelector):
    """
    RefetchSelector tests.
    """

    @pytest.fixture
    def selector(self):
        """
        Returns a new refetch selector.
        """
        return RefetchSelector()

    def test_filter_unchanged_for_unchanged(self, selector, story):
        """
        Tests `filter_unchanged` keeps unchanged stories.
        """
        old = self.populate(story, 0)
        new = self.populate(story, 0)

        selected = selector.filter_unchanged(old, new)

        assert selected is new

    def test_filter_unchanged_missing_old_date(self, selector, story):
        """
        Tests `filter_unchanged` keeps stories when missing old date.
        """
        old = self.populate(story, None)
        new = self.populate(story, 1)

        selected = selector.filter_unchanged(old, new)

        assert selected is new

    def test_filter_unchanged_missing_new_date(self, selector, story):
        """
        Tests `filter_unchanged` keeps stories when missing new date.
        """
        old = self.populate(story, 1)
        new = self.populate(story, None)

        selected = selector.filter_unchanged(old, new)

        assert selected is new

    def test_revived_selection(self, selector, story):
        """
        Tests behavior for stories that have not updated.
        """
        old = self.populate(story, 1)
        new = self.populate(story, 1)

        selected = selector(old, new)

        assert selected is new
        assert UpdateStatus.UPDATED in new.flavors
