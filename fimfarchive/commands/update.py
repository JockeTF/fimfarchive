"""
Update command.
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
import traceback
from argparse import ArgumentParser, Namespace, FileType
from os.path import basename
from typing import Any, Iterable, Iterator, Optional

import arrow
from jmespath import compile as jmes

from fimfarchive.fetchers import (
    Fetcher, FimfarchiveFetcher, Fimfiction2Fetcher, FimfictionFetcher,
)
from fimfarchive.flavors import UpdateStatus
from fimfarchive.selectors import Selector, RefetchSelector, UpdateSelector
from fimfarchive.signals import SignalReceiver
from fimfarchive.stories import Story
from fimfarchive.tasks import UpdateTask

from .base import Command


__all__ = (
    'UpdateCommand',
)


ACCESS_TOKEN_KEY = 'FIMFICTION_ACCESS_TOKEN'


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

    paths = {
        'author': jmes('author.name'),
        'status': jmes('completion_status || status'),
        'words': jmes('num_words || words'),
        'likes': jmes('num_likes || likes'),
        'dislikes': jmes('num_dislikes || dislikes'),
    }

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
        path = self.paths.get(key)

        if path:
            return path.search(meta)
        else:
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
    def approval(self) -> Optional[str]:
        """
        Returns the likes to dislikes ratio, or None.
        """
        likes = self.likes
        dislikes = self.dislikes

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

        if chapters is None:
            return None

        return len(chapters)

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
            print("Action: Missing")

    def on_failure(self, sender, key, error):
        """
        Shows the exception from a failed fetch.
        """
        print("Error:", error)
        traceback.print_exc()


class UpdateCommand(Command):
    """
    Updates stories for Fimfarchive.
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
            '--alpha',
            help="fetch from Fimfiction APIv1",
            action='store_true',
        )

        parser.add_argument(
            '--archive',
            help="previous version of the archive",
            type=FileType('rb'),
            required=True,
            metavar='PATH',
        )

        parser.add_argument(
            '--refetch',
            help="refetch all available stories",
            action='store_true',
        )

        return parser

    def configure(self, opts: Namespace) -> UpdateTask:
        """
        Returns a configured task instance.

        Args:
            opts: Parsed command line arguments.
        """
        fimfarchive: Fetcher
        fimfiction: Fetcher
        selector: Selector

        token = os.environ.get(ACCESS_TOKEN_KEY)

        if opts.alpha:
            fimfiction = FimfictionFetcher()
        elif token:
            fimfiction = Fimfiction2Fetcher(token, True, opts.refetch)
        else:
            exit(f"Environment variable required: {ACCESS_TOKEN_KEY}")

        if opts.refetch:
            selector = RefetchSelector()
        else:
            selector = UpdateSelector()

        print(f"\nStarted: {arrow.now()}")
        print(f"Archive: {basename(opts.archive.name)}")
        print(f"Fetcher: {type(fimfiction).__name__}")
        print(f"Selector: {type(selector).__name__}")

        fimfarchive = FimfarchiveFetcher(opts.archive)

        return UpdateTask(
            fimfarchive=fimfarchive,
            fimfiction=fimfiction,
            selector=selector,
        )

    def __call__(self, *args):
        opts = self.parser.parse_args(args)
        task = self.configure(opts)

        with UpdatePrinter(task):
            task.run()

        print(f"\nDone: {arrow.now()}")

        return 0
