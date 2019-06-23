"""
Writers for Fimfarchive.
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
from copy import deepcopy
from pathlib import Path
from typing import Callable, Iterable, Tuple, Union
from zipfile import ZipFile, ZIP_DEFLATED, ZIP_STORED

from fimfarchive.mappers import (
    DataFormatMapper, StaticMapper, StoryPathMapper, StorySlugMapper,
)
from fimfarchive.stampers import FlavorStamper, PathStamper
from fimfarchive.stories import Story


__all__ = (
    'Writer',
    'DirectoryWriter',
)


PathFunc = Callable[[Story], Union[None, Path, str]]
PathSpec = Union[None, Path, PathFunc, str]


class Writer():
    """
    Abstract base class for story writers.
    """

    def write(self, story: Story) -> None:
        """
        Saves the story to somewhere.

        Args:
            story: Intance of the `Story` class.

        Raises:
            IOError: If writing the story failed.
        """
        raise NotImplementedError()

    def close(self) -> None:
        """
        Finalizes writes and closes files.
        """

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


class DirectoryWriter(Writer):
    """
    Writes story meta and data to file system.
    """

    def __init__(
            self,
            meta_path: PathSpec = None,
            data_path: PathSpec = None,
            overwrite: bool = False,
            make_dirs: bool = True,
            ) -> None:
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

    def get_mapper(self, obj: PathSpec) -> PathFunc:
        """
        Returns a callable for mapping story to file path.
        """
        if callable(obj):
            return obj
        elif isinstance(obj, (Path, str)):
            return StoryPathMapper(obj)
        elif obj is None:
            return StaticMapper(obj)
        else:
            raise TypeError("Path must be callable or string.")

    def check_overwrite(self, path: Path) -> None:
        """
        Checks that a file is not overwritten unless requested.

        Args:
            path: File path which is to be written to.

        Raises:
            FileExistsError: If overwrite is disabled and path exists.
        """
        if not self.overwrite and path.exists():
            raise FileExistsError("Would overwrite: '{}'." .format(path))

    def check_directory(self, path: Path) -> None:
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
        parent = path.parent

        if parent.is_dir():
            return
        elif self.make_dirs:
            parent.mkdir(parents=True)
        else:
            raise FileNotFoundError(parent)

    def perform_write(self, contents: bytes, path: Path) -> None:
        """
        Performs the actual file write.

        Args:
            contents: Bytes to write.
            path: File path to write to.
        """
        self.check_overwrite(path)
        self.check_directory(path)

        path.write_bytes(contents)

    def write_meta(self, story: Story, path: Path) -> None:
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

    def write_data(self, story: Story, path: Path) -> None:
        """
        Prepares the story data for writing.

        Args:
            story: Story containing the data.
            path: File path to write to.
        """
        contents = story.data
        self.perform_write(contents, path)

    def write(self, story: Story) -> None:
        meta_target = self.meta_path(story)
        data_target = self.data_path(story)

        if meta_target is not None:
            meta_path = Path(meta_target).resolve()
            self.write_meta(story, meta_path)

        if data_target is not None:
            data_path = Path(data_target).resolve()
            self.write_data(story, data_path)


class FimfarchiveWriter(Writer):
    """
    Writes stories to a ZIP-file.
    """

    def __init__(
            self,
            path: Union[Path, str],
            extras: Iterable[Tuple[str, bytes]] = (),
            ) -> None:
        """
        Constructor.

        Args:
            path: Output path for the archive.
            extras: Extra names and data to add.
        """
        archive_path = Path(path).resolve(False)
        index_path = archive_path.with_suffix('.json')

        if archive_path.suffix != '.zip':
            raise ValueError(f"Path '{archive_path}' needs zip suffix.")

        if archive_path.exists():
            raise ValueError(f"Path '{archive_path}' already exists.")

        if index_path.exists():
            raise ValueError(f"Path '{index_path}' already exists.")

        self.index_path = index_path
        self.archive_path = archive_path
        self.extras = extras

        self.stamp_format = FlavorStamper(DataFormatMapper())
        self.stamp_path = PathStamper(StorySlugMapper())

        index_path.parent.mkdir(parents=True, exist_ok=True)
        archive_path.parent.mkdir(parents=True, exist_ok=True)

        self.index = index_path.open('wt', encoding='utf8')
        self.archive = ZipFile(archive_path, 'w', ZIP_STORED)

        self.index.write('{\n')
        self.open = True

    def write(self, story: Story) -> None:
        if not self.open:
            raise ValueError("Writer is closed.")

        if story.key != story.meta['id']:
            raise ValueError("Invalid story key.")

        story = story.merge(meta=deepcopy(story.meta))

        self.stamp_format(story)
        self.stamp_path(story)

        path = story.meta['archive']['path']
        meta = json.dumps(story.meta, ensure_ascii=False, sort_keys=True)
        line = f'"{story.key}": {meta},\n'

        self.index.write(line)
        self.archive.writestr(path, story.data, ZIP_STORED)

    def close(self) -> None:
        if not self.open:
            return

        self.open = False

        if 2 < self.index.tell():
            self.index.seek(self.index.tell() - 2)

        self.index.write('\n}\n')
        self.index.close()

        for name, data in self.extras:
            self.archive.writestr(name, data, ZIP_DEFLATED)

        self.archive.write(self.index_path, 'index.json', ZIP_DEFLATED)
        self.archive.close()

        del self.index
        del self.archive
