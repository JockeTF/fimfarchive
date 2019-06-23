"""
Writer tests.
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


import json
import os
from functools import partial
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pytest

from fimfarchive.flavors import DataFormat
from fimfarchive.mappers import StoryPathMapper, StorySlugMapper
from fimfarchive.stampers import PathStamper
from fimfarchive.stories import Story
from fimfarchive.writers import DirectoryWriter, FimfarchiveWriter


class TestDirectoryWriter:
    """
    DirectoryWriter tests.
    """

    @pytest.fixture
    def mapper(self, tmpdir):
        """
        Returns a story path mapper for a temporary directory.
        """
        return StoryPathMapper(tmpdir)

    def test_story_meta_is_written(self, story, mapper):
        """
        Tests story meta is written in its entirety.
        """
        writer = DirectoryWriter(meta_path=mapper)
        writer.write(story)

        with open(mapper(story), 'rt') as fobj:
            assert story.meta == json.load(fobj)

    def test_story_data_is_written(self, story, mapper):
        """
        Tests story data is written in its entirety.
        """
        writer = DirectoryWriter(data_path=mapper)
        writer.write(story)

        with open(mapper(story), 'rb') as fobj:
            assert story.data == fobj.read()

    def test_string_paths_become_mappers(self, tmpdir):
        """
        Tests `StoryPathMapper` instances are created for string paths.
        """
        writer = DirectoryWriter(meta_path='meta', data_path='data')

        assert isinstance(writer.meta_path, StoryPathMapper)
        assert isinstance(writer.data_path, StoryPathMapper)

    def test_rejects_integer_path(self):
        """
        Tests `TypeError` is raised for invalid path types.
        """
        with pytest.raises(TypeError):
            DirectoryWriter(meta_path=1)  # type: ignore

    def test_parent_directory_creation(self, story, tmpdir):
        """
        Tests parent directory is created by default.
        """
        directory = str(tmpdir.join('meta'))

        writer = DirectoryWriter(meta_path=directory)
        writer.write(story)

        assert os.path.isdir(directory)

    def test_disable_directory_creation(self, story, tmpdir):
        """
        Tests `FileNotFoundError` is raised if directory creation is disabled.
        """
        directory = str(tmpdir.join('meta'))

        writer = DirectoryWriter(meta_path=directory, make_dirs=False)

        with pytest.raises(FileNotFoundError):
            writer.write(story)

    def test_refuse_meta_overwrite(self, story, mapper):
        """
        Tests raises `FileExistsError` on meta unless overwrite is enabled.
        """
        writer = DirectoryWriter(meta_path=mapper)

        with open(mapper(story), 'at'):
            pass

        with pytest.raises(FileExistsError):
            writer.write(story)

    def test_refuse_data_overwrite(self, story, mapper):
        """
        Tests raises `FileExistsError` on data unless overwrite is enabled.
        """
        writer = DirectoryWriter(data_path=mapper)

        with open(mapper(story), 'ab'):
            pass

        with pytest.raises(FileExistsError):
            writer.write(story)

    def test_overwrites_when_enabled(self, story, tmpdir):
        """
        Tests overwrites meta and data when requested.
        """
        meta_path = StoryPathMapper(tmpdir.mkdir('meta'))
        data_path = StoryPathMapper(tmpdir.mkdir('data'))

        writer = DirectoryWriter(
            meta_path=meta_path,
            data_path=data_path,
            overwrite=True,
        )

        with open(meta_path(story), 'wt'):
            pass

        with open(data_path(story), 'wb'):
            pass

        writer.write(story)

        with open(meta_path(story), 'rt') as meta_stream:
            assert story.meta == json.load(meta_stream)

        with open(data_path(story), 'rb') as data_stream:
            assert story.data == data_stream.read()

    def test_current_directory_check(self, story):
        """
        Tests directory check for current directory.
        """
        writer = DirectoryWriter()
        writer.check_directory(Path('key'))


class TestFimfarchiveWriter:
    """
    FimfarchiveWriter tests.
    """

    def story(self, key, title, author, name) -> Story:
        """
        Returns a dummy story for writing.
        """
        stream = BytesIO()

        with ZipFile(stream, 'w') as zobj:
            zobj.writestr('text', "Story {key}")

        meta = {
            'id': key,
            'title': title,
            'author': {
                'id': author,
                'name': name,
            },
        }

        return Story(
            key=key,
            fetcher=None,
            meta=meta,
            data=stream.getvalue(),
            flavors=[DataFormat.EPUB],
        )

    @pytest.fixture
    def stories(self):
        """
        Returns a collection of stories to write.
        """
        return (
            self.story(32, "Floof", 48, "Floofer"),
            self.story(64, "Poof", 80, "Poofer"),
        )

    @pytest.fixture
    def extras(self):
        """
        Returns extra data to write.
        """
        return (
            ('about.json', b'about'),
            ('readme.pdf', b'readme'),
        )

    @pytest.fixture
    def archive(self, tmpdir, stories, extras):
        """
        Returns an archive as a ZipFile instance.
        """
        archive = Path(tmpdir) / 'archive.zip'

        with FimfarchiveWriter(archive, extras) as writer:
            for story in stories:
                writer.write(story)

        return ZipFile(BytesIO(archive.read_bytes()))

    def test_meta(self, stories, archive):
        """
        Tests index looks as expected.
        """
        stamp = PathStamper(StorySlugMapper())

        for story in stories:
            stamp(story)

        dumps = partial(json.dumps, ensure_ascii=False, sort_keys=True)
        first, second = tuple(dumps(story.meta) for story in stories)
        raw = f'{{\n"32": {first},\n"64": {second}\n}}\n'

        assert json.loads(archive.read('index.json').decode())
        assert raw.encode() == archive.read('index.json')

    def test_data(self, stories, archive):
        """
        Tests archive includes story data.
        """
        index = json.loads(archive.read('index.json').decode())

        for story in stories:
            data = story.data
            meta = index[str(story.key)]
            path = meta['archive']['path']

            assert data == archive.read(path)

    def test_extras(self, extras, archive):
        """
        Tests archive includes extras.
        """
        for name, data in extras:
            assert data == archive.read(name)
