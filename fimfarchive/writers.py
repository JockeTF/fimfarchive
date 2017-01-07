"""
Writers for Fimfarchive.
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

from fimfarchive.mappers import StaticMapper, StoryPathMapper


__all__ = (
    'Writer',
    'DirectoryWriter',
)


class Writer():
    """
    Abstract base class for story writers.
    """

    def write(self, story):
        """
        Saves the story to somewhere.

        Args:
            story: Intance of the `Story` class.

        throws:
            IOError: If writing the story failed.
        """
        raise NotImplementedError()


class DirectoryWriter(Writer):
    """
    Writes story meta and data to file system.
    """

    def __init__(
            self, meta_path=None, data_path=None,
            overwrite=False, make_dirs=True):
        """
        Constructor.

        Writing of meta and data can be enabled by setting either of
        the path parameters. If both path parameters are set to None,
        then this writer instance will essentially be doing nothing.

        Args:
            meta_path: Directory path, or callable returning a path.
            data_path: Directory path, or callable returning a path.
            overwrite: Enable to overwrite already existing files.
            make_dirs: Enable to create parent directories.
        """
        self.meta_path = self.get_mapper(meta_path)
        self.data_path = self.get_mapper(data_path)
        self.overwrite = overwrite
        self.make_dirs = make_dirs

    def get_mapper(self, obj):
        """
        Returns a callable for mapping story to file path.
        """
        if callable(obj):
            return obj
        elif isinstance(obj, str):
            return StoryPathMapper(obj)
        elif obj is None:
            return StaticMapper(obj)
        else:
            raise TypeError("Path must be callable or string.")

    def check_overwrite(self, path):
        """
        Checks that a file is not overwritten unless requested.

        Args:
            path: File path which is to be written to.

        Raises:
            FileExistsError: If overwrite is disabled and path exists.
        """
        if not self.overwrite and os.path.exists(path):
            raise FileExistsError("Would overwrite: '{}'." .format(path))

    def check_directory(self, path):
        """
        Checks that the path's parent directory exists.

        The parent directory can optionally be created if not.

        Args:
            path: File path which is to be written to.

        Raises:
            IOError: If the parent directory is a file.
            FileNotFoundError: If the parent directory does not exist,
                and if directory creation has been disabled.
        """
        parent = os.path.dirname(path)

        if os.path.isdir(parent):
            return
        elif self.make_dirs:
            os.makedirs(parent)
        else:
            raise FileNotFoundError(parent)

    def perform_write(self, contents, path):
        """
        Performs the actual file write.

        Args:
            contents: Bytes to write.
            path: File path to write to.
        """
        self.check_overwrite(path)
        self.check_directory(path)

        with open(path, 'wb') as fobj:
            fobj.write(contents)

    def write_meta(self, story, path):
        """
        Prepares the story meta for writing.

        Args:
            story: Story containing the meta.
            path: File path to write to.
        """
        text = json.dumps(
            story.meta,
            indent=4,
            sort_keys=True,
            ensure_ascii=False,
        )

        contents = text.encode('utf-8')
        self.perform_write(contents, path)

    def write_data(self, story, path):
        """
        Prepares the story data for writing.

        Args:
            story: Story containing the data.
            path: File path to write to.
        """
        contents = story.data
        self.perform_write(contents, path)

    def write(self, story):
        meta_path = self.meta_path(story)
        data_path = self.data_path(story)

        if meta_path:
            self.write_meta(story, meta_path)

        if data_path:
            self.write_data(story, data_path)
