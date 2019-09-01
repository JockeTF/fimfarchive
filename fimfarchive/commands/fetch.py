"""
Fetch command.
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
import re
from argparse import ArgumentParser, Namespace
from collections import defaultdict
from typing import Dict

from colorama import init as colorize, Fore

from fimfarchive.fetchers import Fimfiction2Fetcher
from fimfarchive.mappers import StorySlugMapper
from fimfarchive.signals import SignalReceiver
from fimfarchive.tasks import FetchTask
from fimfarchive.writers import DirectoryWriter

from .base import Command


__all__ = (
    'FetchCommand',
)


ACCESS_TOKEN_KEY = 'FIMFICTION_ACCESS_TOKEN'


class FetchPrinter(SignalReceiver):
    """
    Prints fetcher progress.
    """

    def __init__(self, task, mapper: StorySlugMapper) -> None:
        self.results: Dict[str, int] = defaultdict(int)
        self.slugify = mapper
        colorize(autoreset=True)
        super().__init__(task)

    def on_attempt(self, sender, key):
        print(f"[{key:>8}] ", end='')
        self.results['attempt'] += 1

    def on_success(self, sender, key, story):
        slug = self.slugify(story)
        print(f"{Fore.GREEN}-->", slug)
        self.results['success'] += 1

    def on_failure(self, sender, key, error):
        print(f"{Fore.RED}<!> {error}")
        self.results['failure'] += 1


class FetchCommand(Command):
    """
    Fetches stories from Fimfiction.
    """

    def __init__(self):
        self.pattern = re.compile(r'/story/(?P<key>\d+)/')
        self.slugify = StorySlugMapper('{story}.{extension}')

    def extract(self, key: str) -> int:
        """
        Extrats a story key from an argument.
        """
        key = key.strip('\t\n\r /')

        try:
            return int(key)
        except ValueError:
            pass

        match = self.pattern.search(key)

        if match is not None:
            return int(match.group('key'))

        raise ValueError(f"Invalid argument: {key}")

    @property
    def parser(self) -> ArgumentParser:
        """
        Returns a command line arguments parser.
        """
        parser = ArgumentParser(prog='', description=self.__doc__)
        parser.add_argument('stories', nargs='+')

        return parser

    def configure(self, opts: Namespace) -> FetchTask:
        token = os.environ.get(ACCESS_TOKEN_KEY)
        writer = DirectoryWriter(data_path=self.slugify)

        if token:
            fimfiction = Fimfiction2Fetcher(token)
        else:
            exit(f"Environment variable required: {ACCESS_TOKEN_KEY}")

        try:
            keys = sorted({self.extract(key) for key in opts.stories})
        except ValueError as error:
            exit(f"{error}")

        return FetchTask(keys, fimfiction, writer)

    def __call__(self, *args: str) -> int:
        opts = self.parser.parse_args(args)
        task = self.configure(opts)

        with FetchPrinter(task, self.slugify) as printer:
            task.run()

        results = printer.results

        if results['failure'] != 0:
            return 1

        return 0
