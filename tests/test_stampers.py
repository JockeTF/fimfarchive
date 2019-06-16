"""
Stamper tests.
"""


#
# Fimfarchive, preserves stories from Fimfiction.
# Copyright (C) 2019  Joakim Soderlund
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

from fimfarchive.flavors import DataFormat, MetaFormat, UpdateStatus
from fimfarchive.mappers import StaticMapper
from fimfarchive.stampers import (
    Stamper, FlavorStamper, PathStamper, UpdateStamper,
)


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

        assert meta['archive'] is original
        assert archive is original


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


class TestFlavorStamper:
    """
    FlavorStamper tests.
    """

    @pytest.mark.parametrize('value', (None, ''))
    def test_ignored_blank_value(self, story, value):
        """
        Tests blank values are ignored.
        """
        stamp = FlavorStamper(StaticMapper(value))
        stamp(story)

        assert value not in story.flavors

    @pytest.mark.parametrize('value', (
        DataFormat.EPUB,
        MetaFormat.ALPHA,
    ))
    def test_stamped_value(self, story, value):
        """
        Tests values are stamped to stories.
        """
        stamp = FlavorStamper(StaticMapper(value))
        stamp(story)

        assert value in story.flavors


class TestPathStamper:
    """
    PathStamper tests.
    """

    @pytest.mark.parametrize('value', (None, 'Some'))
    def test_cleared_alpha_path(self, story, value):
        """
        Tests removal of old alpha format values.
        """
        story = story.merge(meta={
            **story.meta,
            'path': 'path',
        })

        meta = story.meta
        assert 'path' in meta

        stamp = PathStamper(StaticMapper(value))
        stamp(story)

        assert 'path' not in meta

    def test_cleared_beta_path(self, story):
        """
        Tests removal of old beta format values.
        """
        story = story.merge(meta={
            **story.meta,
            'archive': {
                'path': 'path',
            },
        })

        archive = story.meta['archive']
        assert 'path' in archive

        stamp = PathStamper(StaticMapper(None))
        stamp(story)

        assert 'path' not in archive

    @pytest.mark.parametrize('value', (None, ''))
    def test_ignored_blank_value(self, story, value):
        """
        Tests blank values are ignored.
        """
        stamp = PathStamper(StaticMapper(value))
        stamp(story)

        assert 'path' not in story.meta['archive']

    @pytest.mark.parametrize('value', ('one', 'two'))
    def test_stamped_value(self, story, value):
        """
        Tests values are stamped to story meta.
        """
        stamp = PathStamper(StaticMapper(value))
        stamp(story)

        assert value == story.meta['archive']['path']
