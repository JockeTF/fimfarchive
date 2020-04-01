"""
Build command.
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


from argparse import ArgumentParser, Namespace, FileType

from fimfarchive.fetchers import DirectoryFetcher, FimfarchiveFetcher
from fimfarchive.flavors import DataFormat
from fimfarchive.tasks import BuildTask
from fimfarchive.utils import tqdm

from .base import Command


__all__ = (
    'BuildCommand',
)


class BuildCommand(Command):
    """
    Builds a new Fimfarchive release.
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

        parser.add_argument(
            '--output',
            help="directory for the output archive",
            default='worktree/build',
        )

        parser.add_argument(
            '--meta',
            help="directory to fetch meta from",
            default='worktree/update/meta',
        )

        parser.add_argument(
            '--data',
            help="directory to fetch data from",
            default='worktree/render/epub',
        )

        parser.add_argument(
            '--extras',
            help="directory to fetch extras from",
            default='worktree/extras',
        )

        return parser

    def configure(self, opts: Namespace) -> BuildTask:
        """
        Returns a configured task instance.

        Args:
            opts: Parsed command line arguments.
        """
        fimfarchive = FimfarchiveFetcher(
            source=opts.archive,
        )

        directory = DirectoryFetcher(
            meta_path=opts.meta,
            data_path=opts.data,
            flavors=[DataFormat.EPUB],
        )

        return BuildTask(
            output=opts.output,
            upcoming=tqdm(directory),
            previous=fimfarchive,
            extras=opts.extras,
        )

    def __call__(self, *args):
        opts = self.parser.parse_args(args)
        task = self.configure(opts)

        task.run()

        return 0
