"""
Build task.
"""


#
# Fimfarchive, preserves stories from Fimfiction.
# Copyright (C) 2020  Joakim Soderlund
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


from pathlib import Path
from typing import Iterable, Iterator, Optional, Tuple, Union

import arrow

from fimfarchive.converters import LocalUtcConverter
from fimfarchive.exceptions import InvalidStoryError, StorySourceError
from fimfarchive.fetchers import Fetcher
from fimfarchive.stories import Story
from fimfarchive.utils import is_blacklisted
from fimfarchive.writers import FimfarchiveWriter


__all__ = (
    'BuildTask',
)


PathArg = Union[Path, str]


class BuildTask:
    """
    Build a new version of the archive.
    """

    def __init__(
            self,
            output: PathArg,
            upcoming: Iterable[Story],
            previous: Fetcher = None,
            extras: PathArg = None,
            ) -> None:
        """
        Constructor.

        Args:
            output: Directory for the output
            upcoming: Upcoming archive content
            previous: Previous archive content
            extras: Directory for extra files
        """
        self.previous = previous
        self.upcoming = upcoming

        self.convert = LocalUtcConverter()
        self.output = self.get_output(output)
        self.extras = self.get_extras(extras)

    def get_output(self, directory: PathArg) -> Path:
        """
        Returns the complete path for the new archive.

        Args:
            directory: Path for the new archive
        """
        date = arrow.utcnow().format('YYYYMMDD')
        path = Path(directory).resolve(True)
        name = f'fimfarchive-{date}.zip'

        return path / name

    def get_extras(
            self,
            directory: Optional[PathArg]
            ) -> Iterator[Tuple[str, bytes]]:
        """
        Yields extra archive data.

        Args:
            directory: Path to read extras from
        """
        if directory is None:
            return ()

        for path in Path(directory).iterdir():
            yield path.name, path.read_bytes()

    def revive(self, story: Story) -> Story:
        """
        Returns a story containing data from the previous archive.

        Args:
            story: The story to revive

        Raises:
            StorySourceError: If story data is missing
        """
        if self.previous is None:
            raise StorySourceError("Missing previous fetcher.")

        try:
            revived = self.previous.fetch(story.key)
        except InvalidStoryError as e:
            raise StorySourceError("Missing revived story.") from e
        else:
            return story.merge(data=revived.data)

    def resolve(self, story: Story) -> Story:
        """
        Returns a story guaranteed to contain data.

        Args:
            strory: The story to resolve

        Raises:
            StorySourceError: If story data is missing
        """
        try:
            story.data
        except InvalidStoryError:
            return self.revive(story)
        else:
            return story

    def generate(self) -> Iterator[Story]:
        """
        Yields stories for the new archive.
        """
        for story in self.upcoming:
            if is_blacklisted(story):
                continue

            converted = self.convert(story)
            resolved = self.resolve(converted)

            yield resolved

    def run(self):
        with FimfarchiveWriter(self.output, self.extras) as writer:
            for story in self.generate():
                writer.write(story)
