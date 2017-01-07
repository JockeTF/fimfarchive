"""
Writer tests.
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


import json
import os

import pytest

from fimfarchive.mappers import StoryPathMapper
from fimfarchive.writers import DirectoryWriter


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
            DirectoryWriter(meta_path=1)

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

        with open(meta_path(story), 'rt') as fobj:
            assert story.meta == json.load(fobj)

        with open(data_path(story), 'rb') as fobj:
            assert story.data == fobj.read()
