"""
Command base class.
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


from abc import ABC, abstractmethod


__all__ = (
    'Command',
)


class Command(ABC):
    """
    Command line interface for tasks.
    """

    @abstractmethod
    def __call__(self, *args: str) -> int:
        """
        Runs the command.

        Args:
            *args: Command line arguments.

        Returns:
            Application exit status.

        Raises:
            SystemExit: If the arguments are invalid.
        """
