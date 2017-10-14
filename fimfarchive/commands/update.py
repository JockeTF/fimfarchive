"""
Update command.
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


import traceback
from argparse import ArgumentParser, FileType
from typing import Any, Iterable, Iterator, Optional

from jmespath import search

from fimfarchive.fetchers import FimfarchiveFetcher, FimfictionFetcher
from fimfarchive.flavors import UpdateStatus
from fimfarchive.signals import SignalReceiver
from fimfarchive.stories import Story
from fimfarchive.tasks import UpdateTask

from .base import Command


__all__ = (
    'UpdateCommand',
)


class StoryFormatter(Iterable[str]):
    """
    Generates a text representation of story meta.
    """
    attrs = (
        'title',
        'author',
        'status',
        'words',
        'likes',
        'dislikes',
        'approval',
        'chapters',
        'action',
    )

    def __init__(self, story: Story) -> None:
        """
        Constructor.

        Args:
            story: Instance to represent.
        """
        self.story = story

    def __getattr__(self, key: str) -> Any:
        """
        Returns a value from story meta, or None.
        """
        meta = self.story.meta
        return meta.get(key)

    def __iter__(self) -> Iterator[str]:
        """
        Yields the text representation line by line.
        """
        for attr in self.attrs:
            label = attr.capitalize()
            value = getattr(self, attr)
            yield f"{label}: {value}"

    def __str__(self) -> str:
        """
        Returns the entire text representation.
        """
        return '\n'.join(self)

    @property
    def author(self) -> Optional[str]:
        """
        Returns the name of the author, or None.
        """
        meta = self.story.meta
        return search('author.name', meta)

    @property
    def approval(self) -> Optional[str]:
        """
        Returns the likes to dislikes ratio, or None.
        """
        meta = self.story.meta
        likes = meta.get('likes')
        dislikes = meta.get('dislikes')

        try:
            ratio = likes / (likes + dislikes)
        except TypeError:
            return None
        except ZeroDivisionError:
            return f"{0:.0%}"
        else:
            return f"{ratio:.0%}"

    @property
    def chapters(self) -> Optional[int]:
        """
        Returns the number of chapters, or None.
        """
        meta = self.story.meta
        chapters = meta.get('chapters')

        try:
            return len(chapters)
        except TypeError:
            return None

    @property
    def action(self) -> Optional[str]:
        """
        Returns the `UpdateStatus` name, or None.
        """
        for flavor in self.story.flavors:
            if isinstance(flavor, UpdateStatus):
                return flavor.name.capitalize()

        return None


class UpdatePrinter(SignalReceiver):
    """
    Prints story information.
    """

    def on_attempt(self, sender, key, skips, retries):
        """
        Shows an upcoming fetch attempt.
        """
        print(f"\nStory: {key}")

        if retries:
            print(f"Retries: {retries}")
        else:
            print(f"Skips: {skips}")

    def on_success(self, sender, key, story):
        """
        Shows the story from a successful fetch.
        """
        print(StoryFormatter(story))

    def on_skipped(self, sender, key, story):
        """
        Shows information from a skipped fetch.
        """
        if story:
            print(StoryFormatter(story))
        else:
            print("Status: Missing")

    def on_failure(self, sender, key, error):
        """
        Shows the exception from a failed fetch.
        """
        print("Error:", error)
        traceback.print_exc()


class UpdateCommand(Command):
    """
    Fetches updates from Fimfiction.
    """

    @property
    def parser(self) -> ArgumentParser:
        """
        Returns a command line arguments parser.
        """
        parser = ArgumentParser(
            prog='',
            description=self.__doc__,
        )

        parser.add_argument(
            '--archive',
            help="previous version of the archive",
            type=FileType('rb'),
            required=True,
            metavar='PATH',
        )

        return parser

    def __call__(self, *args):
        opts = self.parser.parse_args(args)

        task = UpdateTask(
            fimfarchive=FimfarchiveFetcher(opts.archive),
            fimfiction=FimfictionFetcher(),
        )

        with UpdatePrinter(task):
            task.run()

        return 0
