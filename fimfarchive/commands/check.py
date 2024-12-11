"""
Check command.
"""


#
# Fimfarchive, preserves stories from Fimfiction.
# Copyright (C) 2024  Joakim Soderlund
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


from argparse import ArgumentParser
from io import BytesIO
from zipfile import ZipFile

from fimfarchive.fetchers import FimfarchiveFetcher
from fimfarchive.utils import tqdm

from .base import Command


class CheckCommand(Command):
    """
    Checks archive and story integrity.
    """

    @property
    def parser(self) -> ArgumentParser:
        """
        Returns a command line arguments parser.
        """
        parser = ArgumentParser(prog='', description=self.__doc__)
        parser.add_argument('archive', help="file to check")

        return parser

    def __call__(self, *args: str) -> int:
        opts = self.parser.parse_args(args)
        fetcher = FimfarchiveFetcher(opts.archive)

        if fetcher.archive.testzip() is not None:
            exit("Invalid CRC: Archive")

        for story in tqdm(fetcher, leave=True):
            with ZipFile(BytesIO(story.data)) as zobj:
                if zobj.testzip() is not None:
                    exit(f"Invalid CRC: {story.key}")

        return 0
