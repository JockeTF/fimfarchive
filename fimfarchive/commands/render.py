"""
Render command.
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


from argparse import ArgumentParser, Namespace
from pathlib import Path

import arrow

from fimfarchive.signals import SignalReceiver
from fimfarchive.tasks import RenderTask
from fimfarchive.utils import tqdm

from .base import Command


__all__ = (
    'RenderCommand',
)


class RenderPrinter(SignalReceiver):

    def on_enter(self, sender, keys, workers, spec):
        self.entered = arrow.utcnow()
        print(f"\nStarted: {self.entered}")
        print(f"Directory: {spec.worktree}")
        print(f"Stories: {len(keys)}")
        print(f"Workers: {workers}\n")
        self.tqdm = tqdm(total=len(keys))

    def on_success(self, sender, key):
        self.tqdm.update()

    def on_failure(self, sender, key, error):
        self.tqdm.write(f"[{key:6}] {error}")
        self.tqdm.update()

    def on_exit(self, sender, converted, remaining):
        self.tqdm.close()
        self.exited = arrow.utcnow()
        print(f"\nDone: {self.exited}")
        print(f"Duration: {self.exited - self.entered}")
        print(f"Converted: {len(converted)}")
        print(f"Remaining: {len(remaining)}\n")


class RenderCommand(Command):
    """
    Renders updates as EPUB files.
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
            '--worktree',
            help="Working directory for the archive",
            metavar='PATH',
            default='worktree',
        )

        return parser

    def configure(self, opts: Namespace) -> RenderTask:
        """
        Returns a configured task instance.

        Args:
            opts: Parsed command line arguments.
        """
        worktree = Path(opts.worktree).resolve()

        if not worktree.is_dir():
            self.parser.error(f"No such directory: {worktree}")

        return RenderTask(str(worktree))

    def __call__(self, *args):
        opts = self.parser.parse_args(args)
        task = self.configure(opts)

        with RenderPrinter(task):
            task.run()

        return 0
