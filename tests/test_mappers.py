"""
Mapper tests.
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


import os
from typing import no_type_check, Dict, Any
from unittest.mock import patch, MagicMock, PropertyMock

import pytest

from fimfarchive.exceptions import InvalidStoryError
from fimfarchive.flavors import MetaFormat
from fimfarchive.mappers import (
    MetaFormatMapper, StaticMapper, StoryDateMapper, StoryPathMapper
)
from fimfarchive.stories import Story


CHAPTERS = 'chapters'
MODIFIED = 'date_modified'


class TestStaticMapper:
    """
    StaticMapper tests.
    """

    @pytest.fixture
    def value(self):
        """
        Returns a unique instance.
        """
        return object()

    def test_value(self, story, value):
        """
        Tests returns the supplied value.
        """
        mapper = StaticMapper(value)
        assert mapper(story) is value


class TestStoryDateMapper:
    """
    StoryDateMapper tests.
    """

    @pytest.fixture
    def mapper(self):
        """
        Returns a new StoryDateMapper.
        """
        return StoryDateMapper()

    def merge(self, story, meta):
        """
        Returns a cloned story containing the supplied meta.
        """
        return Story(
            key=story.key,
            fetcher=None,
            meta=meta,
            data=story.data,
            flavors=story.flavors,
        )

    def test_missing_story(self, mapper):
        """
        Tests `None` is returned when story is `None`.
        """
        assert mapper(None) is None

    def test_invalid_story(self, mapper, story):
        """
        Tests `None` is returned when `InvalidStoryError` is raised.
        """
        with patch.object(Story, 'meta', new_callable=PropertyMock) as m:
            m.side_effect = InvalidStoryError

            assert mapper(story) is None
            assert m.called_once_with(story)

    def test_empty_meta(self, mapper, story):
        """
        Tests `None` is returned when meta is empty.
        """
        story = story.merge(meta=dict())

        assert mapper(story) is None

    def test_meta_without_dates(self, mapper, story):
        """
        Tests `None` is returned when meta contains no dates.
        """
        meta: Dict[str, Any] = {
            CHAPTERS: [
                dict(),
                dict(),
                dict(),
            ],
        }

        story = story.merge(meta=meta)

        assert mapper(story) is None

    def test_meta_without_chapters(self, mapper, story):
        """
        Tests timestamp is returned when no chapters are present.
        """
        meta = {
            MODIFIED: 5,
        }

        story = story.merge(meta=meta)

        assert mapper(story).timestamp == 5

    def test_meta_with_none_chapters(self, mapper, story):
        """
        Tests timestamp is returned when chapters is `None`.
        """
        meta = {
            MODIFIED: 5,
            CHAPTERS: None,
        }

        story = story.merge(meta=meta)

        assert mapper(story).timestamp == 5

    def test_meta_with_empty_chapters(self, mapper, story):
        """
        Tests timestamp is returned when chapters is empty.
        """
        meta = {
            MODIFIED: 5,
            CHAPTERS: [],
        }

        story = story.merge(meta=meta)

        assert mapper(story).timestamp == 5

    def test_meta_with_only_chapter_dates(self, mapper, story):
        """
        Tests timestamp is returned when only chapter dates are present.
        """
        meta = {
            CHAPTERS: [
                {MODIFIED: 3},
                {MODIFIED: 5},
                {MODIFIED: 4},
            ],
        }

        story = story.merge(meta=meta)

        assert mapper(story).timestamp == 5

    def test_meta_with_only_story_date(self, mapper, story):
        """
        Tests timestamp is returned when only story date is present.
        """
        meta = {
            MODIFIED: 5,
            CHAPTERS: [
                dict(),
                dict(),
                dict(),
            ],
        }

        story = story.merge(meta=meta)

        assert mapper(story).timestamp == 5

    def test_meta_with_latest_chapter_date(self, mapper, story):
        """
        Tests latests timestamp is returned when in chapter dates.
        """
        meta = {
            MODIFIED: 3,
            CHAPTERS: [
                {MODIFIED: 1},
                {MODIFIED: 5},
                {MODIFIED: 3},
            ],
        }

        story = story.merge(meta=meta)

        assert mapper(story).timestamp == 5

    def test_meta_with_latest_story_date(self, mapper, story):
        """
        Tests latest timestamp is returned when in story date.
        """
        meta = {
            MODIFIED: 5,
            CHAPTERS: [
                {MODIFIED: 1},
                {MODIFIED: 3},
                {MODIFIED: 2},
            ],
        }

        story = story.merge(meta=meta)

        assert mapper(story).timestamp == 5

    def test_meta_with_both_latest(self, mapper, story):
        """
        Tests latest timestamp is returned when in both.
        """
        meta = {
            MODIFIED: 5,
            CHAPTERS: [
                {MODIFIED: 1},
                {MODIFIED: 5},
                {MODIFIED: 3},
            ],
        }

        story = story.merge(meta=meta)

        assert mapper(story).timestamp == 5


class TestStoryPathMapper:
    """
    StoryPathMapper tests.
    """

    def test_joins_paths(self, story):
        """
        Tests returns directory joined with story key.
        """
        directory = os.path.join('some', 'directory')
        path = os.path.join(directory, str(story.key))

        mapper = StoryPathMapper(directory)

        assert mapper(story) == path

    @no_type_check
    def test_casts_values(self, tmpdir, story):
        """
        Tests casts all values to string when joining.
        """
        directory = MagicMock()
        directory.__str__.return_value = 'dir'

        story.key = MagicMock()
        story.key.__str__.return_value = 'key'

        mapper = StoryPathMapper(directory)

        assert mapper(story) == os.path.join('dir', 'key')
        assert directory.__str__.called_once_with()
        assert story.key.__str__.called_once_with()


class TestMetaFormatMapper:
    """
    MetaFormatMapper tests.
    """

    @pytest.fixture
    def mapper(self):
        """
        Returns a meta format mapper instance.
        """
        return MetaFormatMapper()

    @pytest.fixture(params=['likes', 'dislikes', 'words'])
    def alpha(self, request):
        """
        Returns an alpha meta key.
        """
        return request.param

    @pytest.fixture(params=['num_likes', 'num_dislikes', 'num_words'])
    def beta(self, request):
        """
        Returns a beta meta key.
        """
        return request.param

    def merge(self, story, *keys):
        """
        Returns a story containing the requested meta keys.
        """
        meta = {key: i for i, key in enumerate(keys, 1)}
        return story.merge(meta=meta)

    def test_alpha_format(self, mapper, story, alpha):
        """
        Tests alpha meta format is detected.
        """
        story = self.merge(story, alpha, 'misc')
        assert mapper(story) == MetaFormat.ALPHA

    def test_beta_format(self, mapper, story, beta):
        """
        Tests beta meta format is detected.
        """
        story = self.merge(story, beta, 'misc')
        assert mapper(story) == MetaFormat.BETA

    def test_conflict(self, mapper, story, alpha, beta):
        """
        Tests None is returned for conflicting meta keys.
        """
        story = self.merge(story, alpha, beta)
        assert mapper(story) is None

    def test_existing_flavor(self, mapper, story, beta):
        """
        Tests existing flavor takes precedence over meta.
        """
        story = story.merge(flavors=[MetaFormat.ALPHA])
        story = self.merge(story, beta, 'misc')

        assert mapper(story) is MetaFormat.ALPHA
