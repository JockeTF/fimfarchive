"""
Mapper tests.
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


import os
from io import BytesIO
from pathlib import Path
from typing import Any, Dict
from unittest.mock import patch, MagicMock, PropertyMock
from zipfile import ZipFile

import pytest

from fimfarchive.exceptions import InvalidStoryError
from fimfarchive.flavors import DataFormat, MetaFormat
from fimfarchive.mappers import (
    DataFormatMapper, MetaFormatMapper, StaticMapper,
    StoryDateMapper, StoryPathMapper, StorySlugMapper,
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

        assert mapper(story).int_timestamp == 5

    def test_meta_with_none_chapters(self, mapper, story):
        """
        Tests timestamp is returned when chapters is `None`.
        """
        meta = {
            MODIFIED: 5,
            CHAPTERS: None,
        }

        story = story.merge(meta=meta)

        assert mapper(story).int_timestamp == 5

    def test_meta_with_empty_chapters(self, mapper, story):
        """
        Tests timestamp is returned when chapters is empty.
        """
        meta = {
            MODIFIED: 5,
            CHAPTERS: [],
        }

        story = story.merge(meta=meta)

        assert mapper(story).int_timestamp == 5

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

        assert mapper(story).int_timestamp == 5

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

        assert mapper(story).int_timestamp == 5

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

        assert mapper(story).int_timestamp == 5

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

        assert mapper(story).int_timestamp == 5

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

        assert mapper(story).int_timestamp == 5


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

        assert mapper(story) == Path(path)

    def test_casts_values(self, tmpdir, story):
        """
        Tests casts all values to string when joining.
        """
        mapper = StoryPathMapper('dir')

        story.key = MagicMock()
        story.key.__str__.return_value = 'key'

        assert mapper(story) == Path('dir', 'key')
        assert story.key.__str__.called_once_with()


class TestStorySlugMapper:
    """
    StorySlugMapper tests.
    """

    @pytest.fixture
    def mapper(self) -> StorySlugMapper:
        """
        Returns a mapper instance.
        """
        return StorySlugMapper()

    @pytest.fixture
    def story(self, story: Story) -> Story:
        """
        Returns a story instance.
        """
        meta = {
            'id': 1337,
            'title': 'title',
            'author': {
                'id': 42,
                'name': 'name',
            },
        }

        return story.merge(
            meta=meta,
            flavors=[DataFormat.EPUB]
        )

    def test_mapping(self, mapper, story):
        """
        Tests a simple slug mapping.
        """
        assert mapper(story) == 'epub/n/name-42/title-1337.epub'

    def test_custom_mapping(self, story):
        """
        Tests a slug mapping with a custom template.
        """
        mapper = StorySlugMapper('{story}.{extension}')

        assert mapper(story) == 'title-1337.epub'

    @pytest.mark.parametrize('text,result', (
        ('Project Sunflower: Harmony', 'project_sunflower_harmony'),
        ('The Enchanted Library', 'the_enchanted_library'),
        ('Hurricane\'s Way', 'hurricanes_way'),
        ('Sharers\' Day', 'sharers_day'),
        ('Paca ' * 32, ('paca_' * 22)[:-1]),
        ('Paca' * 32, ''),
        (None, 'none'),
        ('  ', ''),
        (' ', ''),
        ('', ''),
    ))
    def test_slugify(self, mapper, text, result):
        """
        Tests creating a slug for a title.
        """
        assert mapper.slugify(text) == result

    @pytest.mark.parametrize('key,slug,result', (
        (16, 'slug', 'slug-16'),
        (32, None, '32'),
        (64, '', '64'),
    ))
    def test_join(self, mapper, key, slug, result):
        """
        Tests joining a slug with a key.
        """
        assert mapper.join(key, slug) == result

    def test_join_with_negative_key(self, mapper):
        """
        Tests `ValueError` is raised when joining a negative key.
        """
        with pytest.raises(ValueError):
            mapper.join('-1', 'slug')

    @pytest.mark.parametrize('slug,result', (
        ('alpaca', 'a'),
        ('pony', 'p'),
        ('42', '_'),
        ('  ', '_'),
        (' ', '_'),
        ('', '_'),
    ))
    def test_group(self, mapper, slug, result):
        """
        Tests grouping of a slug.
        """
        assert mapper.group(slug) == result

    @pytest.mark.parametrize('flavors,result', (
        ({MetaFormat.BETA, DataFormat.EPUB}, 'epub'),
        ({DataFormat.EPUB}, 'epub'),
        ({DataFormat.HTML}, 'html'),
        ({MetaFormat.BETA}, 'data'),
        ({}, 'data'),
    ))
    def test_classify(self, mapper, story, flavors, result):
        """
        Tests classify with a story.
        """
        story = story.merge(flavors=flavors)

        assert mapper.classify(story) == result

    def test_map_with_long_template(self, story):
        """
        Tests `ValueError` is raised when result is too long.
        """
        mapper = StorySlugMapper('paca' * 256)

        with pytest.raises(ValueError):
            mapper(story)


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
        assert mapper(story) is MetaFormat.ALPHA

    def test_beta_format(self, mapper, story, beta):
        """
        Tests beta meta format is detected.
        """
        story = self.merge(story, beta, 'misc')
        assert mapper(story) is MetaFormat.BETA

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


class TestDataFormatMapper:
    """
    DataFormatMapper tests.
    """

    @pytest.fixture
    def mapper(self):
        """
        Returns a data format mapper instance.
        """
        return DataFormatMapper()

    def zip(self, names) -> bytes:
        """
        Returns a populated ZIP-file as bytes.
        """
        data = BytesIO()

        with ZipFile(data, 'w') as zobj:
            for name in names:
                zobj.writestr(name, name)

        return data.getvalue()

    @pytest.mark.parametrize('data', [
        b'{}',
        b'{"id": 42}',
        b'{"id": 42}\n',
    ])
    def test_json_mapping(self, mapper, story, data):
        """
        Tests detection of JSON data format.
        """
        story = story.merge(data=data, flavors=[])

        assert DataFormat.JSON is mapper(story)

    @pytest.mark.parametrize('files', [
        ['mimetype', 'book.ncx', 'book.opf'],
        ['mimetype', 'book.opf', 'book.ncx', 'Chapter1.html'],
    ])
    def test_fpub_mapping(self, mapper, story, files):
        """
        Tests detection of FPUB data format.
        """
        story = story.merge(data=self.zip(files), flavors=[])

        assert DataFormat.FPUB is mapper(story)

    @pytest.mark.parametrize('files', [
        ['mimetype', 'content.opf', 'toc.ncx'],
        ['mimetype', 'toc.ncx', 'content.opf', 'Chapter1.html'],
    ])
    def test_epub_mapping(self, mapper, story, files):
        """
        Tests detection of EPUB data format.
        """
        story = story.merge(data=self.zip(files), flavors=[])

        assert DataFormat.EPUB is mapper(story)

    @pytest.mark.parametrize('fmt', [
        DataFormat.EPUB,
        DataFormat.JSON,
    ])
    def test_included_mapping(self, mapper, story, fmt):
        """
        Tests detection of included flavor.
        """
        story = story.merge(flavors=[fmt])

        assert fmt is mapper(story)

    @pytest.mark.parametrize('data', [
        b'',
        b'P',
        b'PK',
        b'PK\x03',
        b'PK\x03\x03',
    ])
    def test_unknown_raw_mapping(self, mapper, story, data):
        """
        Tests unknown raw data returns no flavor.
        """
        story = story.merge(data=data, flavors=[])

        assert None is mapper(story)

    @pytest.mark.parametrize('files', [
        [],
        ['alpaca.jpg'],
        ['book.opf', 'book.ncx'],
        ['mimetype', 'book.ncx'],
        ['content.opf', 'tox.ncx', 'Chapter1.html'],
    ])
    def test_unknown_zip_mapping(self, mapper, story, files):
        """
        Tests unknown ZIP data returns no flavor.
        """
        story = story.merge(data=self.zip(files), flavors=[])

        assert None is mapper(story)
