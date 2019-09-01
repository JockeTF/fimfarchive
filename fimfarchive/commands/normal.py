"""
Normalize command.
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


from pathlib import Path

from fimfarchive.converters import LocalUtcConverter
from fimfarchive.fetchers import DirectoryFetcher
from fimfarchive.utils import tqdm
from fimfarchive.writers import DirectoryWriter


from .base import Command


__all__ = (
    'NormalCommand',
)


class NormalCommand(Command):
    """
    Normalizes updated story meta.
    """

    def __call__(self, *args: str) -> int:
        convert = LocalUtcConverter()
        fetcher = DirectoryFetcher(meta_path=Path('worktree/update/meta'))
        writer = DirectoryWriter(meta_path='worktree/normal/meta')

        for story in tqdm(fetcher):
            story = convert(story)
            writer.write(story)

        return 0
