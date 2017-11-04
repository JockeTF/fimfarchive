"""
Stamper tests.
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


from unittest.mock import patch
from typing import Dict

import arrow
import pytest

from fimfarchive.flavors import UpdateStatus
from fimfarchive.stampers import Stamper, UpdateStamper


class TestStamper:
    """
    Stamper tests.
    """

    @pytest.fixture
    def stamper(self):
        """
        Returns a new stamper instance.
        """
        return Stamper()

    def test_missing_archive_dict(self, stamper, story):
        """
        Tests archive dict is created if none exists.
        """
        meta = story.meta
        assert 'archive' not in meta

        archive = stamper.get_archive(story)
        assert meta['archive'] is archive

    def test_existing_archive_dict(self, stamper, story):
        """
        Tests archive dict is kept if it exists.
        """
        meta = story.meta
        original: Dict = dict()
        meta['archive'] = original
        archive = stamper.get_archive(story)

        assert archive is original
        assert meta['archive'] is original


class TestUpdateStamper:
    """
    UpdateStamper tests.
    """

    @pytest.fixture
    def time(self):
        """
        Returns a timestamp for the mocked utcnow.
        """
        stamp = arrow.get(1)

        with patch('arrow.utcnow') as m:
            m.return_value = stamp
            yield stamp.isoformat()

    @pytest.fixture
    def stamper(self, time):
        """
        Returns an update stamper instance.
        """
        return UpdateStamper()

    def test_created_story(self, stamper, story, time):
        """
        Tests timestamps are added for created stories.
        """
        story.flavors.add(UpdateStatus.CREATED)
        stamper(story)

        archive = story.meta['archive']
        assert archive['date_checked'] == time
        assert archive['date_created'] == time
        assert archive['date_fetched'] == time
        assert archive['date_updated'] == time

    def test_updated_story(self, stamper, story, time):
        """
        Tests timestamps are added for updated stories.
        """
        story.flavors.add(UpdateStatus.UPDATED)
        stamper(story)

        archive = story.meta['archive']
        assert archive['date_checked'] == time
        assert archive['date_created'] is None
        assert archive['date_fetched'] == time
        assert archive['date_updated'] == time

    def test_revived_story(self, stamper, story, time):
        """
        Tests timestamps are added for revived stories.
        """
        story.flavors.add(UpdateStatus.REVIVED)
        stamper(story)

        archive = story.meta['archive']
        assert archive['date_checked'] == time
        assert archive['date_created'] is None
        assert archive['date_fetched'] == time
        assert archive['date_updated'] is None

    def test_deleted_story(self, stamper, story, time):
        """
        Tests timestamps are added for deleted stories.
        """
        story.flavors.add(UpdateStatus.DELETED)
        stamper(story)

        archive = story.meta['archive']
        assert archive['date_checked'] == time
        assert archive['date_created'] is None
        assert archive['date_fetched'] is None
        assert archive['date_updated'] is None

    def test_created_modification(self, stamper, story, time):
        """
        Tests existing timestamps are replaced for created stories.
        """
        story.flavors.add(UpdateStatus.CREATED)
        prev = arrow.get(-1).isoformat()

        story.meta['archive'] = {
            'date_checked': prev,
            'date_created': prev,
            'date_fetched': prev,
            'date_updated': prev,
        }

        stamper(story)
        assert prev != time

        archive = story.meta['archive']
        assert archive['date_checked'] == time
        assert archive['date_created'] == time
        assert archive['date_fetched'] == time
        assert archive['date_updated'] == time

    def test_deleted_modification(self, stamper, story, time):
        """
        Tests existing timestamps are kept for deleted stories.
        """
        story.flavors.add(UpdateStatus.DELETED)
        prev = arrow.get(-1).isoformat()

        story.meta['archive'] = {
            'date_checked': prev,
            'date_created': prev,
            'date_fetched': prev,
            'date_updated': prev,
        }

        stamper(story)
        assert prev != time

        archive = story.meta['archive']
        assert archive['date_checked'] == time
        assert archive['date_created'] == prev
        assert archive['date_fetched'] == prev
        assert archive['date_updated'] == prev
