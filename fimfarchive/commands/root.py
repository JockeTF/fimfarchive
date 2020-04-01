"""
Root command.
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


from typing import Dict, Type

from .base import Command
from .build import BuildCommand
from .update import UpdateCommand


__all__ = (
    'RootCommand',
)


class RootCommand(Command):
    """
    The main application command.
    """
    commands: Dict[str, Type[Command]] = {
        'build': BuildCommand,
        'update': UpdateCommand,
    }

    def load(self, command: str) -> Command:
        """
        Instantiates a command.

        Args:
            command: Name of the command to instantiate.

        Returns:
            An instance of the specified command.

        Raises:
            KeyError: If the command does not exist.
        """
        return self.commands[command]()

    def doc(self, command: str, adjust=1, indent=2) -> str:
        """
        Generates documentation for a single command.

        Args:
            command: Name of the command to document.
            adjust: Number of spaces before the command summary.
            indent: Number of spaces before the command name.

        Returns:
            A name and summary for the command.
        """
        cls = self.load(command)
        doc = getattr(cls, '__doc__', None)

        if doc:
            doc = str(doc).strip()
            doc = doc.split('\n', 1)[0]

        description = [
            indent * ' ',
            command.ljust(adjust),
            str(doc),
        ]

        return ''.join(description)

    @property
    def usage(self) -> str:
        """
        Generates a list of the available commands.

        Returns:
            A usage help text for the application.
        """
        text = [
            'Usage: COMMAND [PARAMETERS]\n\n',
            'Fimfarchive, ensuring that history is preseved.\n\n',
        ]

        if not self.commands:
            return ''.join(text).strip()

        commands = sorted(cmd for cmd in self.commands.keys())
        adjust = max(len(cmd) for cmd in commands) + 2

        text.append('Commands:\n')
        for command in commands:
            line = self.doc(command, adjust)
            text.extend((line, '\n'))

        return ''.join(text).strip()

    def __call__(self, *args: str) -> int:
        try:
            cmd = self.load(args[0])
        except (IndexError, KeyError):
            exit(self.usage)
        else:
            return cmd(*args[1:])
